import threading
import time
import mss
import numpy as np
import cv2
from pynput import mouse as pynput_mouse
from pynput import keyboard as pynput_keyboard
from pynput.keyboard import Key

class FishingBot:
    def __init__(self, app):
        self.app = app
        # macOS controllers (use app's controllers if available)
        self.mouse = getattr(app, 'mouse_controller', pynput_mouse.Controller())
        self.keyboard = getattr(app, 'keyboard_controller', pynput_keyboard.Controller())
        self._retina_scale = 1.0
        self.recovery_in_progress = False
        self.watchdog_active = False
        self.watchdog_thread = None
        self.last_loop_heartbeat = time.time()
        self.force_stop_flag = False
        self.last_fruit_spawn_time = 0  # Track when last fruit spawn was detected
        self.fruit_spawn_cooldown = 15 * 60  # 15 minutes cooldown after detecting spawn
    
    def check_recovery_needed(self):
        """Smart recovery check - detects genuinely stuck states"""
        if not self.app.recovery_enabled or not self.app.main_loop_active or self.recovery_in_progress:
            return False
            
        current_time = time.time()
        
        # Check every 20 seconds
        if current_time - self.app.last_smart_check < 20.0:
            return False
            
        self.app.last_smart_check = current_time
        
        # Check if current state has been running too long
        state_duration = current_time - self.app.state_start_time
        
        # Reasonable timeouts for each state
        max_durations = {
            "idle": 45.0,           # Between fishing cycles
            "fishing": 90.0,        # Active fishing with fish control
            "casting": 20.0,        # Casting the line
            "menu_opening": 15.0,   # Opening purchase menu
            "typing": 10.0,         # Typing purchase amount
            "clicking": 8.0,        # Individual clicks
            "purchasing": 60.0      # Full purchase sequence
        }
        
        max_duration = max_durations.get(self.app.current_state, 60.0)
        
        if state_duration > max_duration:
            self.app.log(f'🚨 State "{self.app.current_state}" stuck for {state_duration:.0f}s (max: {max_duration}s)', "error")
            return True
            
        # Check for complete activity freeze
        time_since_activity = current_time - self.app.last_activity_time
        if time_since_activity > 120:  # 2 minutes of no activity
            self.app.log(f'⚠️ No activity for {time_since_activity:.0f}s - loop may be frozen', "error")
            return True
            
        return False
    
    def start_watchdog(self):
        """Start aggressive watchdog that monitors from OUTSIDE the main loop"""
        if self.watchdog_active:
            return
            
        self.watchdog_active = True
        self.last_loop_heartbeat = time.time()
        self.watchdog_thread = threading.Thread(target=self._watchdog_monitor, daemon=True)
        self.watchdog_thread.start()
        self.app.log('🐕 Watchdog started - monitoring for stuck states', "verbose")
    
    def stop_watchdog(self):
        """Stop the watchdog"""
        self.watchdog_active = False
        if self.watchdog_thread and self.watchdog_thread.is_alive():
            self.watchdog_thread.join(timeout=2.0)
    
    def _watchdog_monitor(self):
        """Smart watchdog that monitors for stuck states and restarts the loop"""
        while self.watchdog_active and self.app.main_loop_active:
            try:
                current_time = time.time()
                
                # Check heartbeat from main loop
                heartbeat_age = current_time - self.last_loop_heartbeat
                
                # Trigger recovery if no heartbeat for 30 seconds
                if heartbeat_age > 30.0:
                    self.app.log(f'🚨 WATCHDOG: No heartbeat for {heartbeat_age:.0f}s - Loop appears stuck', "error")
                    self._restart_fishing_loop()
                    break
                
                # Check for stuck states
                if self.check_recovery_needed():
                    self.app.log('🚨 WATCHDOG: Stuck state detected - Restarting loop', "error")
                    self._restart_fishing_loop()
                    break
                
                time.sleep(10.0)  # Check every 10 seconds
                
            except Exception as e:
                self.app.log(f'⚠️ Watchdog error: {e}', "error")
                time.sleep(10.0)
        
        self.app.log('🐕 Watchdog stopped', "verbose")
    
    def update_heartbeat(self):
        """Update heartbeat from main loop"""
        self.last_loop_heartbeat = time.time()
    
    def _restart_fishing_loop(self):
        """Restart the fishing loop when it gets stuck"""
        if self.recovery_in_progress:
            return
            
        current_time = time.time()
        
        # Limit restart attempts
        if self.app.recovery_count >= 5:
            self.app.log(f'🛑 TOO MANY RESTARTS: {self.app.recovery_count} attempts. Stopping fishing.', "error")
            self.app.main_loop_active = False
            self.watchdog_active = False
            return
        
        self.recovery_in_progress = True
        self.app.recovery_count += 1
        self.app.last_recovery_time = current_time
        
        self.app.log(f'🔄 RESTARTING LOOP #{self.app.recovery_count}/5 - Fishing got stuck', "important")
        
        # Clean up mouse state immediately
        try:
            if self.app.is_clicking:
                self.mouse.release(pynput_mouse.Button.left)
                self.app.is_clicking = False
        except Exception:
            pass
        
        # Set force stop flag to exit current loop
        self.force_stop_flag = True
        
        # Reset state
        self.app.last_activity_time = current_time
        self.app.last_fish_time = current_time
        self.app.set_recovery_state("idle", {"action": "loop_restart"})
        
        # Wait a moment for current loop to exit
        time.sleep(2.0)
        
        # Reset flags and restart
        self.force_stop_flag = False
        self.last_loop_heartbeat = time.time()
        
        # Start fresh loop
        self.app.log('🎣 Starting fresh fishing loop...', "important")
        self.app.main_loop_thread = threading.Thread(target=lambda: self.run_main_loop(skip_initial_setup=True), daemon=True)
        self.app.main_loop_thread.start()
        
        self.recovery_in_progress = False

    def _force_recovery(self):
        """NUCLEAR OPTION: Force recovery when system is truly stuck"""
        if self.recovery_in_progress:
            return
            
        current_time = time.time()
        
        # Recovery limit
        if self.app.recovery_count >= 3:
            self.app.log(f'🛑 RECOVERY LIMIT REACHED: {self.app.recovery_count} attempts failed. STOPPING EVERYTHING.', "error")
            self.app.main_loop_active = False
            self.watchdog_active = False
            return
        
        self.recovery_in_progress = True
        self.app.recovery_count += 1
        self.app.last_recovery_time = current_time
        
        self.app.log(f'💥 FORCE RECOVERY #{self.app.recovery_count}/3 - NUKING EVERYTHING', "error")
        
        # Send webhook
        if hasattr(self.app, 'webhook_manager'):
            recovery_info = {
                "recovery_number": self.app.recovery_count,
                "stuck_state": self.app.current_state,
                "timestamp": current_time,
                "recovery_type": "FORCE_RECOVERY"
            }
            self.app.webhook_manager.send_recovery(recovery_info)
        
        # FORCE stop everything
        self.force_stop_flag = True
        self.app.main_loop_active = False
        
        # Release mouse IMMEDIATELY
        try:
            self.mouse.release(pynput_mouse.Button.left)
            self.app.is_clicking = False
        except Exception:
            pass
        
        # Reset ALL state
        self.app.last_activity_time = current_time
        self.app.last_fish_time = current_time
        self.app.set_recovery_state("idle", {"action": "force_recovery_reset"})
        
        # AGGRESSIVE thread cleanup - don't wait nicely
        self.app.log('💥 FORCE KILLING main loop thread...', "verbose")
        time.sleep(1.0)  # Brief pause for force_stop_flag to take effect
        
        # Try to join thread, but don't wait forever
        try:
            if hasattr(self.app, 'main_loop_thread') and self.app.main_loop_thread and self.app.main_loop_thread.is_alive():
                self.app.main_loop_thread.join(timeout=3.0)
                if self.app.main_loop_thread.is_alive():
                    self.app.log('⚠️ Thread refused to die - continuing anyway', "error")
        except:
            pass
        
        # RESTART FROM SCRATCH
        if self.app.recovery_count < 3:
            self.app.log('💥 RESTARTING FROM SCRATCH...', "important")
            
            # Reset flags
            self.force_stop_flag = False
            self.last_loop_heartbeat = time.time()
            
            # Start fresh
            self.app.main_loop_active = True
            self.app.main_loop_thread = threading.Thread(target=lambda: self.run_main_loop(skip_initial_setup=True), daemon=True)
            self.app.main_loop_thread.start()
            
            self.app.log('✅ FORCE RECOVERY COMPLETE - Fresh start initiated', "important")
        
        self.recovery_in_progress = False
    
    def perform_recovery(self):
        """Legacy recovery method - now just calls force recovery"""
        self._force_recovery()
    
    def cast_line(self):
        """Cast fishing line"""
        # Always move to optimal fishing position before casting
        self.move_to_fishing_position()
        
        # Right-click to clear any menus before casting
        try:
            print(f"🖱️ Right-clicking at fishing position")
            current_pos = self.mouse.position
            self.app._right_click_at(current_pos)
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Right-click failed: {e}")
        
        # Cast the line
        print("Casting line...")
        self.app.cast_line()
    
    def store_fruit(self):
        """Complete fruit storage and rod switching workflow with reliable delays"""
        fruit_storage_enabled = getattr(self.app, 'fruit_storage_enabled', False)
        print(f"🔍 Fruit storage enabled: {fruit_storage_enabled}")
        
        if not fruit_storage_enabled:
            print("⏭️ Fruit storage disabled - skipping")
            return
            
        try:
            import time
            
            # Get configured keys from GUI settings
            fruit_key = getattr(self.app, 'fruit_storage_key', '3')
            rod_key = getattr(self.app, 'rod_key', '1')
            
            print(f"🍎 Starting fruit storage workflow with enhanced delays...")
            
            # Step 1: Press the configured fruit storage key
            print(f"📦 Step 1: Pressing fruit storage key '{fruit_key}'")
            try:
                self.keyboard.press(fruit_key)
                self.keyboard.release(fruit_key)
            except Exception:
                pass
            time.sleep(0.5)  # Increased delay for inventory to fully open
            
            # Step 2: Click at the configured fruit point
            if hasattr(self.app, 'fruit_coords') and 'fruit_point' in self.app.fruit_coords:
                fruit_x, fruit_y = self.app.fruit_coords['fruit_point']
                print(f"🎯 Step 2: Clicking fruit point at ({fruit_x}, {fruit_y})")
                self.app._click_at((fruit_x, fruit_y))
                time.sleep(0.3)  # Increased delay before storage action
            else:
                print("❌ Fruit point coordinates not configured - skipping fruit storage")
                return
            
            # Step 2.5: Try to store fruit and wait
            print(f"📦 Step 2.5: Attempting fruit storage...")
            time.sleep(1.2)  # Increased wait for storage attempt to fully process
            
            # Step 2.6: Drop fruit with backspace (fallback)
            print(f"⬇️ Step 2.6: Dropping fruit with backspace...")
            try:
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
            except Exception:
                pass
            time.sleep(1.0)  # Increased wait for drop animation to complete
            
            # Step 3: Ensure proper rod equipping (single press only)
            print(f"🎣 Step 3: Returning to rod...")
            
            # Wait longer for game to settle completely
            time.sleep(1.0)  # Extended wait to ensure game state is stable
            
            # Single rod key press - pressing twice cycles through items!
            print(f"🎣 Step 3: Pressing rod key '{rod_key}' once")
            try:
                self.keyboard.press(rod_key)
                self.keyboard.release(rod_key)
            except Exception:
                pass
            time.sleep(0.8)  # Extended wait for rod to be fully equipped
            
            # Step 4: Click at the configured bait point
            if hasattr(self.app, 'fruit_coords') and 'bait_point' in self.app.fruit_coords:
                bait_x, bait_y = self.app.fruit_coords['bait_point']
                print(f"🎯 Step 4: Clicking bait point at ({bait_x}, {bait_y})")
                self.app._click_at((bait_x, bait_y))
                time.sleep(0.3)  # Increased delay after bait selection
            else:
                print("❌ Bait point coordinates not configured - skipping bait selection")
                return
            
            # Step 5: Final wait and move to fishing position
            print(f"🎯 Step 5: Final preparation for next cast...")
            time.sleep(0.3)  # Final settling delay
            self.move_to_fishing_position()
            
            print(f"✅ Fruit storage sequence completed with enhanced timing: Key {fruit_key} → Fruit Point → Storage/Drop → Rod Key x2 → Bait Point → Fishing Position")
            
        except Exception as e:
            print(f"❌ Fruit storage workflow failed: {e}")
    
    def move_to_fishing_position(self):
        """Move mouse to fishing position (custom or default center-top)"""
        try:
            import time
            
            # Use custom fishing location if set, otherwise use default
            if hasattr(self.app, 'fishing_location') and self.app.fishing_location:
                fishing_x, fishing_y = self.app.fishing_location
                print(f"🎯 Moving mouse to custom fishing position: ({fishing_x}, {fishing_y})")
            else:
                # Fallback to default center-top position
                screen_width = self.app.root.winfo_screenwidth()
                screen_height = self.app.root.winfo_screenheight()
                fishing_x = screen_width // 2
                fishing_y = screen_height // 3
                print(f"🎯 Moving mouse to default fishing position: ({fishing_x}, {fishing_y})")
            
            # Only move mouse to position, don't click yet
            self.mouse.position = (fishing_x, fishing_y)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Failed to move to fishing position: {e}")
    
    def check_and_purchase(self):
        """Check if auto-purchase is needed"""
        if getattr(self.app, 'auto_purchase_var', None) and self.app.auto_purchase_var.get():
            self.app.purchase_counter += 1
            loops_needed = int(getattr(self.app, 'loops_per_purchase', 1)) if getattr(self.app, 'loops_per_purchase', None) is not None else 1
            print(f'🛒 Purchase counter: {self.app.purchase_counter}/{loops_needed}')
            if self.app.purchase_counter >= max(1, loops_needed):
                try:
                    print('🛒 Performing auto-purchase...')
                    self.perform_auto_purchase()
                    self.app.purchase_counter = 0
                    print('🛒 Auto-purchase complete')
                except Exception as e:
                    print(f'❌ AUTO-PURCHASE ERROR: {e}')
                    # Reset purchase counter to prevent getting stuck
                    self.app.purchase_counter = 0
                    # Reset state to idle
                    self.app.set_recovery_state("idle", {"action": "purchase_error_recovery"})
    
    def perform_auto_purchase(self):
        """Perform auto-purchase sequence"""
        pts = self.app.point_coords
        
        # Convert points to tuples if they're lists (from JSON)
        for key in [1, 2, 3]:
            if key in pts and pts[key] and isinstance(pts[key], list):
                pts[key] = tuple(pts[key])
        
        if not pts or not pts.get(1) or not pts.get(2) or not pts.get(3):
            print("❌ Auto-purchase failed: Missing point coordinates (need points 1-3)")
            return
        
        if not self.app.main_loop_active:
            return
        
        print(f"🛒 Starting auto-purchase sequence for {self.app.auto_purchase_amount} items...")
        
        amount = str(self.app.auto_purchase_amount)
        
        # Purchase sequence with state tracking
        self.app.set_recovery_state("menu_opening", {"action": "pressing_e_key"})
        try:
            self.keyboard.press('e')
            self.keyboard.release('e')
        except Exception:
            pass
        time.sleep(self.app.purchase_delay_after_key)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_1"})
        self._click_at(pts[1])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_2"})
        self._click_at(pts[2])
        # Longer delay to ensure input field is ready
        time.sleep(self.app.purchase_click_delay + 0.3)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("typing", {"action": "typing_amount"})
        # Clear field first, then type amount more slowly
        # macOS: use Command+A to select all
        try:
            self.keyboard.press(Key.cmd)
            self.keyboard.press('a')
            self.keyboard.release('a')
            self.keyboard.release(Key.cmd)
        except Exception:
            pass
        time.sleep(0.1)
        try:
            self.keyboard.press(Key.delete)
            self.keyboard.release(Key.delete)
        except Exception:
            pass
        time.sleep(0.1)
        
        # Type each character with small delay for reliability
        for char in amount:
            try:
                self.keyboard.type(char)
            except Exception:
                pass
            time.sleep(0.05)
        
        # Extra delay to ensure typing is complete
        time.sleep(self.app.purchase_after_type_delay + 0.5)
        print(f"🛒 Typed amount: {amount}")
        
        if not self.app.main_loop_active:
            return
        
        # Continue purchase sequence
        self.app.set_recovery_state("clicking", {"action": "click_point_1_confirm"})
        self._click_at(pts[1])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_3"})
        self._click_at(pts[3])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_2_final"})
        self._click_at(pts[2])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "right_click_fishing_location"})
        # Use custom fishing location or default center-top
        if hasattr(self.app, 'fishing_location') and self.app.fishing_location:
            fishing_coords = self.app.fishing_location
            print(f"🎯 Right-clicking at custom fishing location: {fishing_coords}")
        else:
            # Fallback to default center-top position
            screen_width = self.app.root.winfo_screenwidth()
            screen_height = self.app.root.winfo_screenheight()
            fishing_coords = (screen_width // 2, screen_height // 3)
            print(f"🎯 Right-clicking at default fishing location: {fishing_coords}")
        
        self._right_click_at(fishing_coords)
        time.sleep(self.app.purchase_click_delay)
        
        if hasattr(self.app, 'webhook_manager'):
            self.app.webhook_manager.send_purchase(amount)
        
        print(f"✅ Auto-purchase sequence completed for {amount} items")
        
        # Reset state to idle after successful purchase
        self.app.set_recovery_state("idle", {"action": "purchase_complete"})
    
    def _click_at(self, coords):
        """Click at coordinates"""
        try:
            x, y = (int(coords[0]), int(coords[1]))
            self.mouse.position = (x, y)
            self.mouse.press(pynput_mouse.Button.left)
            self.mouse.release(pynput_mouse.Button.left)
        except Exception:
            pass
    
    def _right_click_at(self, coords):
        """Right click at coordinates"""
        try:
            x, y = (int(coords[0]), int(coords[1]))
            self.mouse.position = (x, y)
            threading.Event().wait(0.05)
            self.mouse.press(pynput_mouse.Button.right)
            threading.Event().wait(0.05)
            self.mouse.release(pynput_mouse.Button.right)
        except Exception:
            pass
    
    def validate_fishing_detection(self, img, real_area, target_color, dark_color, white_color):
        """Enhanced validation of fishing bar detection with confidence scoring"""
        try:
            real_height = real_area['height']
            real_width = real_area['width']
            
            # Count color pixels for validation
            blue_pixels = 0
            dark_pixels = 0
            white_pixels = 0
            total_pixels = real_height * real_width
            
            for row_idx in range(real_height):
                for col_idx in range(real_width):
                    b, g, r = img[row_idx, col_idx, 0:3]
                    
                    # Count target color (blue bar) - BGR order
                    if b == target_color[0] and g == target_color[1] and r == target_color[2]:
                        blue_pixels += 1
                    # Count dark areas (fish zones) - BGR order
                    elif b == dark_color[0] and g == dark_color[1] and r == dark_color[2]:
                        dark_pixels += 1
                    # Count white areas (indicator) - BGR order
                    elif b == white_color[0] and g == white_color[1] and r == white_color[2]:
                        white_pixels += 1
            
            # Calculate confidence metrics
            blue_ratio = blue_pixels / total_pixels
            dark_ratio = dark_pixels / total_pixels
            white_ratio = white_pixels / total_pixels
            
            # Validation criteria
            has_sufficient_blue = blue_ratio > 0.05  # At least 5% blue (bar outline)
            has_sufficient_dark = dark_ratio > 0.1   # At least 10% dark (fish area)
            has_white_indicator = white_ratio > 0.02  # At least 2% white (indicator)
            
            # Overall confidence score
            confidence = 0.0
            if has_sufficient_blue:
                confidence += 0.3
            if has_sufficient_dark:
                confidence += 0.4
            if has_white_indicator:
                confidence += 0.3
            
            # Bonus for balanced ratios (good fishing bar should have these proportions)
            if 0.1 < dark_ratio < 0.6 and 0.02 < white_ratio < 0.2:
                confidence += 0.1
            
            validation_result = {
                'is_valid': confidence > 0.6,
                'confidence': confidence,
                'blue_ratio': blue_ratio,
                'dark_ratio': dark_ratio,
                'white_ratio': white_ratio,
                'metrics': {
                    'sufficient_blue': has_sufficient_blue,
                    'sufficient_dark': has_sufficient_dark,
                    'has_white': has_white_indicator
                }
            }
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Detection validation error: {e}")
            return {'is_valid': False, 'confidence': 0.0}

    def auto_locate_bar_area(self, sct, target_color, tolerance):
        """Fallback: scan a larger region to auto-locate the fishing bar when overlay is misaligned.
        Returns an area dict {x,y,width,height} or None.
        """
        try:
            # Screen dimensions
            screen_width = self.app.root.winfo_screenwidth()
            screen_height = self.app.root.winfo_screenheight()

            # Search central band of the screen to avoid UI and wood floor edges
            search_left = int(screen_width * 0.25)
            search_top = int(screen_height * 0.15)
            search_width = int(screen_width * 0.50)
            search_height = int(screen_height * 0.55)

            # Convert logical coords to pixel coords for mss
            monitor = {
                'left': int(search_left * self._retina_scale),
                'top': int(search_top * self._retina_scale),
                'width': int(search_width * self._retina_scale),
                'height': int(search_height * self._retina_scale)
            }

            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            if img.shape[2] == 4:
                img = img[:, :, :3]

            # Coarse scan with stride to reduce cost
            stride_y = max(2, search_height // 200)
            stride_x = max(2, search_width // 200)

            found_x = None
            found_y = None
            for row_idx in range(0, search_height, stride_y):
                row = img[row_idx]
                for col_idx in range(0, search_width, stride_x):
                    b, g, r = row[col_idx, 0:3]
                    if (abs(r - target_color[0]) <= tolerance and
                        abs(g - target_color[1]) <= tolerance and
                        abs(b - target_color[2]) <= tolerance):
                        found_x = search_left + col_idx
                        found_y = search_top + row_idx
                        break
                if found_x is not None:
                    break

            if found_x is None:
                return None

            # Build a reasonable area around the found pixel (matches typical bar size)
            area_width = 200
            area_height = 375
            # Convert back to logical coords from pixel coords
            area_x = max(0, int((found_x - (area_width // 2)) / self._retina_scale))
            area_y = max(0, int((found_y - (area_height // 2)) / self._retina_scale))

            # Clamp within screen
            area_x = min(area_x, screen_width - area_width)
            area_y = min(area_y, screen_height - area_height)

            auto_area = {'x': int(area_x), 'y': int(area_y), 'width': area_width, 'height': area_height}
            print(f"📍 Auto-located bar area: x={auto_area['x']}, y={auto_area['y']}, w={auto_area['width']}, h={auto_area['height']}")
            return auto_area
        except Exception as e:
            print(f"⚠️ Auto-locate error: {e}")
            return None
    
    def calculate_smart_control_zones(self, dark_sections, white_top_y, real_height):
        """Calculate smart control zones with weighted scoring"""
        if not dark_sections or white_top_y is None:
            return None
        
        # Enhanced section analysis
        for section in dark_sections:
            section['size'] = section['end'] - section['start'] + 1
            section['relative_size'] = section['size'] / real_height
            
            # Distance from white indicator (closer = more relevant)
            section['distance_to_white'] = abs(section['middle'] - white_top_y)
            section['relative_distance'] = section['distance_to_white'] / real_height
            
            # Confidence scoring (larger sections closer to white indicator are better)
            size_score = min(1.0, section['relative_size'] / 0.2)  # Normalize to 20% of height
            distance_score = max(0.1, 1.0 - (section['relative_distance'] * 2))  # Closer is better
            
            section['confidence'] = (size_score * 0.6) + (distance_score * 0.4)
            section['control_weight'] = section['confidence'] * section['size']
        
        # Select best section based on weighted scoring
        best_section = max(dark_sections, key=lambda s: s['control_weight'])
        
        return {
            'target_section': best_section,
            'all_sections': dark_sections,
            'section_count': len(dark_sections),
            'total_dark_area': sum(s['size'] for s in dark_sections),
            'confidence': best_section['confidence']
        }
    
    def run_main_loop(self, skip_initial_setup=False):
        """Main fishing loop with enhanced smart detection and control"""
        print('🎣 Main loop started with enhanced smart detection')
        # Align target color with working Windows version (RGB)
        target_color = (85, 170, 255)
        dark_color = (25, 25, 25)
        white_color = (255, 255, 255)
        
        # Simplified control parameters
        self.error_smoothing = []  # Smooth error values for stability
        self.fishing_success_rate = 0.8  # Track success rate for adaptive timeouts
        self.recent_catches = []  # Track recent fishing attempts
        
        # Reset recovery count on fresh start
        if not self.recovery_in_progress:
            self.app.recovery_count = 0
        
        try:
            with mss.mss() as sct:
                # Initial setup sequence (skip if resuming)
                if not skip_initial_setup:
                    self.perform_initial_setup()
                else:
                    print("🔧 Skipping initial setup - resuming from current state")

                # Log Retina scale once for debugging
                try:
                    main_monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    px_w = main_monitor['width']
                    logical_w = self.app.root.winfo_screenwidth()
                    if logical_w:
                        self._retina_scale = max(1.0, px_w / float(logical_w))
                    # Scale detection for macOS Retina displays
                    print(f"🖥️ Retina scale detected: {self._retina_scale:.2f}")
                except Exception as e:
                    print(f"⚠️ Retina scale detection error: {e}")
                
                # Start watchdog AFTER initial setup to prevent interference
                if not self.watchdog_active:
                    self.start_watchdog()
                
                # Main fishing loop
                while self.app.main_loop_active and not self.force_stop_flag:
                    # Update heartbeat for watchdog
                    self.update_heartbeat()
                    
                    # Check if loop should continue
                    if not self.app.main_loop_active:
                        print('🛑 Main loop stopped - main_loop_active is False')
                        break
                    if self.force_stop_flag:
                        print('🛑 Main loop stopped - force_stop_flag is True')
                        break
                    
                    try:
                        print(f'🎣 Fishing cycle #{self.app.fish_count + 1}')
                        
                        # Cast line (bait selection already done in initial setup)
                        # Ensure mouse is not held from prior loop
                        if self.app.is_clicking:
                            try:
                                self.mouse.release(pynput_mouse.Button.left)
                            except Exception:
                                pass
                            self.app.is_clicking = False

                        self.app.set_recovery_state("casting", {"action": "initial_cast"})
                        self.cast_line()
                        cast_time = time.time()
                        
                        # Small delay to ensure rod is properly cast
                        time.sleep(0.5)
                        
                        # Enter detection phase
                        self.app.set_recovery_state("fishing", {"action": "blue_bar_detection"})
                        detected = False
                        was_detecting = False
                        # Require a stable detection window before enabling clicks
                        control_armed = False
                        stable_frames = 0
                        first_detection_time = None
                        MIN_CONTROL_DELAY = 0.6  # seconds to wait after cast before any click
                        print('Scanning for blue fishing bar...')
                        
                        detection_start_time = time.time()
                        last_spawn_check = time.time()
                        spawn_check_interval = 4.0  # Check for spawns every 4 seconds (lightweight)
                        # Allow one global auto-locate attempt per cycle
                        global_bar_search_attempted = False
                        override_bar_area = None
                        
                        while self.app.main_loop_active and not self.force_stop_flag:
                            # Update heartbeat frequently during detection
                            self.update_heartbeat()
                            
                            # Periodically check for fruit spawns (with smart cooldown)
                            # ONLY check when NOT actively fishing (detected == False means waiting for bite)
                            current_time = time.time()
                            time_since_last_spawn = current_time - self.last_fruit_spawn_time
                            
                            # Only check if: NOT actively fishing AND enough time passed AND outside cooldown
                            if not detected and current_time - last_spawn_check > spawn_check_interval and time_since_last_spawn > self.fruit_spawn_cooldown:
                                try:
                                    # Check for spawn text using OCR
                                    if hasattr(self.app, 'ocr_manager') and self.app.ocr_manager.is_available():
                                        # Temporarily disable OCR cooldown for spawn checks
                                        original_cooldown = self.app.ocr_manager.capture_cooldown
                                        self.app.ocr_manager.capture_cooldown = 0.1  # Very short cooldown for spawn detection
                                        
                                        spawn_text = self.app.ocr_manager.extract_text()
                                        
                                        # Restore original cooldown
                                        self.app.ocr_manager.capture_cooldown = original_cooldown
                                        
                                        if spawn_text:
                                            print(f"🔍 Spawn check OCR result: {spawn_text}")
                                            fruit_name = self.app.ocr_manager.detect_fruit_spawn(spawn_text)
                                            if fruit_name:
                                                print(f"🌟 Devil fruit spawn detected: {fruit_name}")
                                                # Record detection time for cooldown
                                                self.last_fruit_spawn_time = current_time
                                                print(f"⏰ Fruit spawn cooldown activated - won't check again for 15 minutes")
                                                # Send webhook
                                                if hasattr(self.app, 'webhook_manager') and getattr(self.app, 'fruit_spawn_webhook_enabled', True):
                                                    self.app.webhook_manager.send_fruit_spawn(fruit_name)
                                    
                                    last_spawn_check = current_time
                                except Exception as spawn_error:
                                    print(f"⚠️ Spawn check error: {spawn_error}")
                            elif time_since_last_spawn <= self.fruit_spawn_cooldown:
                                # Still in cooldown period, skip checking
                                pass
                            
                            # Smart adaptive timeout system
                            current_time = time.time()
                            
                            # Calculate adaptive timeout based on success rate
                            base_timeout = self.app.scan_timeout
                            if self.fishing_success_rate > 0.7:
                                # High success rate - can wait longer for fish
                                adaptive_timeout = base_timeout * 1.3
                            elif self.fishing_success_rate < 0.4:
                                # Low success rate - shorter timeout to try more frequently
                                adaptive_timeout = base_timeout * 0.7
                            else:
                                adaptive_timeout = base_timeout
                            
                            if current_time - detection_start_time > adaptive_timeout:
                                if not detected:
                                    print(f'⏰ No fish detected after {adaptive_timeout:.1f}s (adaptive), recasting...')
                                    # Track failed attempt
                                    self.recent_catches.append(False)
                                    if len(self.recent_catches) > 10:
                                        self.recent_catches.pop(0)
                                    self.fishing_success_rate = sum(self.recent_catches) / len(self.recent_catches)
                                    break
                                elif current_time - detection_start_time > adaptive_timeout + 15:
                                    print(f'⏰ Fish control timeout after {adaptive_timeout + 15:.1f}s, recasting...')
                                    # Clean up mouse state before recasting
                                    if self.app.is_clicking:
                                        try:
                                            self.mouse.release(pynput_mouse.Button.left)
                                        except Exception:
                                            pass
                                        self.app.is_clicking = False
                                    # Track failed attempt
                                    self.recent_catches.append(False)
                                    if len(self.recent_catches) > 10:
                                        self.recent_catches.pop(0)
                                    self.fishing_success_rate = sum(self.recent_catches) / len(self.recent_catches)
                                    break
                            
                            # Get screenshot with error handling
                            try:
                                # Use bar layout area for fishing detection, unless overridden by auto-locate
                                bar_area = override_bar_area or self.app.layout_manager.get_layout_area('bar')
                                if not bar_area:
                                    # Default bar area if not set
                                    bar_area = {'x': 700, 'y': 400, 'width': 200, 'height': 100}
                                    print(f'⚠️ WARNING: Using default bar area {bar_area} - Position overlay properly!')
                                else:
                                    # Only log once at start
                                    if not detected and time.time() - cast_time < 1.0:
                                        print(f'📍 Bar detection area: x={bar_area["x"]}, y={bar_area["y"]}, w={bar_area["width"]}, h={bar_area["height"]}')
                                
                                x = bar_area['x']
                                y = bar_area['y']
                                width = bar_area['width']
                                height = bar_area['height']
                                # Scale coordinates for macOS Retina (logical -> pixels)
                                monitor_px = {
                                    'left': int(x * self._retina_scale),
                                    'top': int(y * self._retina_scale),
                                    'width': int(width * self._retina_scale),
                                    'height': int(height * self._retina_scale)
                                }
                                screenshot = sct.grab(monitor_px)
                                img = np.array(screenshot)
                                
                                # Convert BGRA to BGR (remove alpha channel if present)
                                if img.shape[2] == 4:
                                    img = img[:, :, :3]
                                
                                # Normalize for macOS Retina scaling
                                img_h, img_w = img.shape[0], img.shape[1]
                                if img_w != width or img_h != height:
                                    scale_w = img_w / float(width)
                                    scale_h = img_h / float(height)
                                    self._retina_scale = (scale_w + scale_h) / 2.0
                                    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_NEAREST)
                            except Exception as screenshot_error:
                                print(f'❌ Screenshot error: {screenshot_error}')
                                time.sleep(0.1)
                                continue
                            
                            # Look for blue bar (target color) - with small tolerance for Retina color profile shifts
                            try:
                                point1_x = None
                                point1_y = None
                                found_first = False
                                tolerance = 7  # Allow ±7 variance per channel for Retina display color shifts
                                
                                # Scan for color match with tolerance
                                for row_idx in range(height):
                                    for col_idx in range(width):
                                        b, g, r = img[row_idx, col_idx, 0:3]
                                        rb, gb, bb = int(r), int(g), int(b)
                                        # Match with tolerance to handle Retina color profile shifts
                                        if (abs(rb - target_color[0]) <= tolerance and 
                                            abs(gb - target_color[1]) <= tolerance and 
                                            abs(bb - target_color[2]) <= tolerance):
                                            point1_x = x + col_idx
                                            point1_y = y + row_idx
                                            found_first = True
                                            print(f'✅ Blue bar found at pixel ({col_idx}, {row_idx}) with color (R={r},G={g},B={b})')
                                            break
                                    if found_first:
                                        break
                                
                                # DEBUG: If not found, sample pixels to identify actual colors
                                if not found_first and time.time() - cast_time < 2.0:  # Only log first few attempts
                                    print(f'🔍 DEBUG: No match for target color {target_color} (tolerance±{tolerance}). Sampling pixels...')
                                    sample_colors = {}
                                    for row_idx in range(0, height, max(1, height // 5)):  # Sample 5 rows
                                        for col_idx in range(0, width, max(1, width // 5)):  # Sample 5 cols
                                            b, g, r = img[row_idx, col_idx, 0:3]
                                            color_tuple = (r, g, b)
                                            if color_tuple not in sample_colors:
                                                sample_colors[color_tuple] = 0
                                            sample_colors[color_tuple] += 1
                                    # Print top 5 colors found
                                    sorted_colors = sorted(sample_colors.items(), key=lambda x: x[1], reverse=True)[:5]
                                    print(f'🔍 Top colors in bar area (RGB): {[f"({c[0][0]},{c[0][1]},{c[0][2]})" for c in sorted_colors]}')
                            except Exception as detection_error:
                                print(f'❌ Blue bar detection error: {detection_error}')
                                time.sleep(0.1)
                                continue
                            
                            if found_first:
                                detected = True
                            else:
                                # No blue bar found
                                # Try one-time global auto-locate if overlay area might be wrong
                                if (not detected and not global_bar_search_attempted and
                                    time.time() - cast_time > 0.7):
                                    try:
                                        auto_area = self.auto_locate_bar_area(sct, target_color, tolerance)
                                        global_bar_search_attempted = True
                                        if auto_area:
                                            override_bar_area = auto_area
                                            # Continue loop to re-scan with new area
                                            time.sleep(0.05)
                                            continue
                                        else:
                                            print('⚠️ Global auto-locate did not find the bar. Continuing...')
                                    except Exception as e:
                                        print(f'⚠️ Global search error: {e}')

                                if not detected and time.time() - cast_time > self.app.scan_timeout:
                                    print(f'Cast timeout after {self.app.scan_timeout}s, recasting...')
                                    # Reselect bait in case we ran out (recovery feature)
                                    if hasattr(self.app, 'bait_manager') and self.app.bait_manager.is_enabled():
                                        print("🔄 Reselecting bait (may have run out)")
                                        self.app.bait_manager.select_top_bait()
                                    # Ensure no mouse press sticks between casts
                                    if self.app.is_clicking:
                                        try:
                                            self.mouse.release(pynput_mouse.Button.left)
                                        except Exception:
                                            pass
                                        self.app.is_clicking = False
                                    time.sleep(0.3)
                                    break
                                
                                if was_detecting:
                                    print('Fish caught! Processing...')
                                    
                                    # Clean up mouse state immediately
                                    if self.app.is_clicking:
                                        try:
                                            self.mouse.release(pynput_mouse.Button.left)
                                        except Exception:
                                            pass
                                        self.app.is_clicking = False
                                    
                                    # Track successful catch for adaptive learning
                                    self.recent_catches.append(True)
                                    if len(self.recent_catches) > 10:
                                        self.recent_catches.pop(0)
                                    self.fishing_success_rate = sum(self.recent_catches) / len(self.recent_catches)
                                    
                                    # Increment fish counter when fish is actually caught
                                    self.app.increment_fish_counter()
                                    
                                    # Complete post-catch workflow
                                    self.process_post_catch_workflow()
                                    
                                    time.sleep(self.app.wait_after_loss)
                                    was_detecting = False
                                    self.check_and_purchase()
                                    # Continue to next fishing cycle
                                    success_pct = int(self.fishing_success_rate * 100)
                                    print(f'🐟 Fish processing complete | Success Rate: {success_pct}%')
                                    break
                                
                                time.sleep(0.1)
                                continue
                            
                            # Find right edge of blue bar (with tolerance for Retina)
                            point2_x = None
                            row_idx = point1_y - y
                            for col_idx in range(width - 1, -1, -1):
                                b, g, r = img[row_idx, col_idx, 0:3]
                                rb, gb, bb = int(r), int(g), int(b)
                                if (abs(rb - target_color[0]) <= tolerance and 
                                    abs(gb - target_color[1]) <= tolerance and 
                                    abs(bb - target_color[2]) <= tolerance):
                                    point2_x = x + col_idx
                                    break

                            # As a fallback, assume a thin bar if we couldn't find the right edge
                            if point2_x is None:
                                point2_x = min(x + width - 1, point1_x + 3)
                                detected_bar_width = point2_x - point1_x + 1
                                # Reject bars that are too narrow (likely false positives)
                                if detected_bar_width < 10:
                                    print(f"⚠️ Detected bar too narrow ({detected_bar_width}px); likely false positive at ({point1_x}, {point1_y}). Skipping.")
                                    time.sleep(0.1)
                                    continue
                                print(f"⚠️ Right edge not found; using fallback width from {point1_x} to {point2_x}")
                            
                            # Get the fishing bar area
                            temp_area_x = point1_x
                            temp_area_width = max(1, point2_x - point1_x + 1)
                            
                            # Final sanity check on bar width
                            if temp_area_width < 10:
                                print(f"⚠️ Final bar width too narrow ({temp_area_width}px); skipping detection.")
                                time.sleep(0.1)
                                continue
                            temp_monitor_px = {
                                'left': int(temp_area_x * self._retina_scale),
                                'top': int(y * self._retina_scale),
                                'width': int(temp_area_width * self._retina_scale),
                                'height': int(height * self._retina_scale)
                            }
                            temp_screenshot = sct.grab(temp_monitor_px)
                            temp_img = np.array(temp_screenshot)
                            # Convert BGRA to BGR (remove alpha channel if present)
                            if temp_img.shape[2] == 4:
                                temp_img = temp_img[:, :, :3]
                            # Normalize for Retina
                            t_h, t_w = temp_img.shape[0], temp_img.shape[1]
                            if t_w != temp_area_width or t_h != height:
                                temp_img = cv2.resize(temp_img, (temp_area_width, height), interpolation=cv2.INTER_NEAREST)
                            
                            # Find top and bottom of dark area
                            top_y = None
                            for row_idx in range(height):
                                found_dark = False
                                for col_idx in range(temp_area_width):
                                    b, g, r = temp_img[row_idx, col_idx, 0:3]
                                    rb, gb, bb = int(r), int(g), int(b)
                                    if (abs(rb - dark_color[0]) <= 20 and
                                        abs(gb - dark_color[1]) <= 20 and
                                        abs(bb - dark_color[2]) <= 20):
                                        top_y = y + row_idx
                                        found_dark = True
                                        break
                                if found_dark:
                                    break
                            
                            bottom_y = None
                            for row_idx in range(height - 1, -1, -1):
                                found_dark = False
                                for col_idx in range(temp_area_width):
                                    b, g, r = temp_img[row_idx, col_idx, 0:3]
                                    rb, gb, bb = int(r), int(g), int(b)
                                    if (abs(rb - dark_color[0]) <= 20 and
                                        abs(gb - dark_color[1]) <= 20 and
                                        abs(bb - dark_color[2]) <= 20):
                                        bottom_y = y + row_idx
                                        found_dark = True
                                        break
                                if found_dark:
                                    break
                            
                            if top_y is None or bottom_y is None:
                                time.sleep(0.1)
                                continue
                            
                            # Get the real fishing area
                            self.app.real_area = {'x': temp_area_x, 'y': top_y, 'width': temp_area_width, 'height': bottom_y - top_y + 1}
                            real_x = self.app.real_area['x']
                            real_y = self.app.real_area['y']
                            real_width = self.app.real_area['width']
                            real_height = self.app.real_area['height']
                            real_monitor_px = {
                                'left': int(real_x * self._retina_scale),
                                'top': int(real_y * self._retina_scale),
                                'width': int(real_width * self._retina_scale),
                                'height': int(real_height * self._retina_scale)
                            }
                            real_screenshot = sct.grab(real_monitor_px)
                            real_img = np.array(real_screenshot)
                            # Convert BGRA to BGR (remove alpha channel if present)
                            if real_img.shape[2] == 4:
                                real_img = real_img[:, :, :3]
                            # Normalize for Retina
                            r_h, r_w = real_img.shape[0], real_img.shape[1]
                            if r_w != real_width or r_h != real_height:
                                real_img = cv2.resize(real_img, (real_width, real_height), interpolation=cv2.INTER_NEAREST)
                            
                            # Skip validation for now - keep it simple
                            
                            # Find white indicator
                            white_top_y = None
                            white_bottom_y = None
                            for row_idx in range(real_height):
                                for col_idx in range(real_width):
                                    b, g, r = real_img[row_idx, col_idx, 0:3]
                                    rb, gb, bb = int(r), int(g), int(b)
                                    if (abs(rb - white_color[0]) <= 30 and
                                        abs(gb - white_color[1]) <= 30 and
                                        abs(bb - white_color[2]) <= 30):
                                        white_top_y = real_y + row_idx
                                        break
                                if white_top_y is not None:
                                    break
                            
                            for row_idx in range(real_height - 1, -1, -1):
                                for col_idx in range(real_width):
                                    b, g, r = real_img[row_idx, col_idx, 0:3]
                                    rb, gb, bb = int(r), int(g), int(b)
                                    if (abs(rb - white_color[0]) <= 30 and
                                        abs(gb - white_color[1]) <= 30 and
                                        abs(bb - white_color[2]) <= 30):
                                        white_bottom_y = real_y + row_idx
                                        break
                                if white_bottom_y is not None:
                                    break
                            
                            if white_top_y is not None and white_bottom_y is not None:
                                white_height = white_bottom_y - white_top_y + 1
                                max_gap = white_height * 2
                            else:
                                # Debug why control didn't start
                                print(f"⚠️ White indicator not found (top={white_top_y}, bottom={white_bottom_y}) in real area w={real_width}, h={real_height}")
                            
                            # Find dark sections (fish position)
                            dark_sections = []
                            current_section_start = None
                            gap_counter = 0
                            for row_idx in range(real_height):
                                has_dark = False
                                for col_idx in range(real_width):
                                    b, g, r = real_img[row_idx, col_idx, 0:3]
                                    rb, gb, bb = int(r), int(g), int(b)
                                    if (abs(rb - dark_color[0]) <= 20 and
                                        abs(gb - dark_color[1]) <= 20 and
                                        abs(bb - dark_color[2]) <= 20):
                                        has_dark = True
                                        break
                                if has_dark:
                                    gap_counter = 0
                                    if current_section_start is None:
                                        current_section_start = real_y + row_idx
                                else:
                                    if current_section_start is not None:
                                        gap_counter += 1
                                        if gap_counter > max_gap:
                                            section_end = real_y + row_idx - gap_counter
                                            dark_sections.append({'start': current_section_start, 'end': section_end, 'middle': (current_section_start + section_end) // 2})
                                            current_section_start = None
                                            gap_counter = 0
                            
                            if current_section_start is not None:
                                section_end = real_y + real_height - 1 - gap_counter
                                dark_sections.append({'start': current_section_start, 'end': section_end, 'middle': (current_section_start + section_end) // 2})
                            
                            # Enhanced smart fishing control with arming to avoid instant reel-in
                            if dark_sections and white_top_y is not None:
                                # Build stability before arming control
                                if first_detection_time is None:
                                    first_detection_time = time.time()
                                stable_frames += 1

                                if (not control_armed and
                                    stable_frames >= 3 and
                                    time.time() - cast_time >= MIN_CONTROL_DELAY):
                                    control_armed = True
                                    was_detecting = True
                                    print('Fish detected! Starting control...')
                                    self.app.set_recovery_state("fishing", {"action": "fish_control_active"})

                                if not control_armed:
                                    # Ensure we are not holding mouse before arming
                                    if self.app.is_clicking:
                                        try:
                                            self.mouse.release(pynput_mouse.Button.left)
                                        except Exception:
                                            pass
                                        self.app.is_clicking = False
                                    time.sleep(0.05)
                                    continue

                                # PD control once armed
                                for section in dark_sections:
                                    section['size'] = section['end'] - section['start'] + 1
                                largest_section = max(dark_sections, key=lambda s: s['size'])

                                raw_error = largest_section['middle'] - white_top_y
                                normalized_error = raw_error / real_height if real_height > 0 else raw_error
                                derivative = normalized_error - self.app.previous_error
                                self.app.previous_error = normalized_error
                                pd_output = self.app.kp * normalized_error + self.app.kd * derivative

                                print(f'Error: {raw_error}px, PD: {pd_output:.2f}')

                                if pd_output > 0:
                                    if not self.app.is_clicking:
                                        try:
                                            self.mouse.press(pynput_mouse.Button.left)
                                        except Exception:
                                            pass
                                        self.app.is_clicking = True
                                else:
                                    if self.app.is_clicking:
                                        try:
                                            self.mouse.release(pynput_mouse.Button.left)
                                        except Exception:
                                            pass
                                        self.app.is_clicking = False
                            else:
                                # More debug to surface why control didn't run
                                if not dark_sections:
                                    print(f"⚠️ No dark sections detected in real area; bar width={real_width}, height={real_height}")
                                if white_top_y is None:
                                    print("⚠️ Missing white indicator; cannot compute error")
                            
                            time.sleep(0.1)
                        
                        self.app.set_recovery_state("idle", {"action": "detection_complete"})
                        
                    except Exception as e:
                        print(f'🚨 Main loop error: {e}')
                        import traceback
                        traceback.print_exc()
                        self.app.log(f'Main loop error: {e}', "error")
                        if not self.force_stop_flag:
                            time.sleep(1.0)
                        else:
                            break  # Exit immediately on force stop
        
        except Exception as e:
            self.app.log(f'🚨 Critical main loop error: {e}', "error")
        
        finally:
            # ALWAYS clean up
            print('🛑 Main loop stopped - cleaning up')
            
            # Stop watchdog
            self.stop_watchdog()
            
            # Clean up mouse state
            if self.app.is_clicking:
                try:
                    self.mouse.release(pynput_mouse.Button.left)
                    self.app.is_clicking = False
                except Exception:
                    pass
    
    def perform_initial_setup(self):
        """Perform initial setup: zoom out, specific zoom in, auto buy if enabled"""
        print("🔧 Performing initial setup...")
        
        # Set state to prevent watchdog interference
        self.app.set_recovery_state("initial_setup", {"action": "starting_setup"})
        
        # Update heartbeat to prevent watchdog from triggering during setup
        self.update_heartbeat()
        
        # Step 1: Auto zoom (only if enabled)
        auto_zoom_enabled = getattr(self.app, 'auto_zoom_var', None) and self.app.auto_zoom_var.get()
        
        if auto_zoom_enabled:
            if hasattr(self.app, 'zoom_controller'):
                if self.app.zoom_controller.is_available():
                    self.app.set_recovery_state("initial_setup", {"action": "zoom_out"})
                    print("🔍 Step 1: Full zoom out...")
                    success_out = self.app.zoom_controller.reset_zoom()
                    print(f"Zoom out result: {success_out}")
                    self.update_heartbeat()  # Update after zoom out
                    time.sleep(1.0)  # Longer delay to ensure zoom completes
                    
                    # Step 2: Specific zoom in
                    self.app.set_recovery_state("initial_setup", {"action": "zoom_in"})
                    print("🔍 Step 2: Specific zoom in...")
                    success_in = self.app.zoom_controller.zoom_in()
                    print(f"Zoom in result: {success_in}")
                    self.update_heartbeat()  # Update after zoom in
                    time.sleep(1.0)  # Longer delay to ensure zoom completes
                else:
                    print("🔍 Zoom controller not available")
            else:
                print("🔍 Zoom controller not initialized")
        else:
            print("🔍 Auto zoom disabled - skipping zoom sequence")
        
        # Step 3: Auto purchase if enabled
        if getattr(self.app, 'auto_purchase_var', None) and self.app.auto_purchase_var.get():
            print("🛒 Step 3: Auto purchase...")
            self.app.set_recovery_state("purchasing", {"sequence": "initial_auto_purchase"})
            self.perform_auto_purchase()
            # Add delay after auto purchase to ensure it completes
            time.sleep(1.0)
        
        # Step 4: Auto bait selection (when rod is in hand)
        if hasattr(self.app, 'bait_manager') and self.app.bait_manager.is_enabled():
            print("🎣 Step 4: Selecting initial bait...")
            self.app.set_recovery_state("initial_setup", {"action": "bait_selection"})
            self.app.bait_manager.select_bait_before_cast()
            time.sleep(0.5)
        
        # Final delay to ensure all setup operations are complete before casting
        self.app.set_recovery_state("initial_setup", {"action": "finalizing"})
        print("⏳ Waiting for setup to stabilize...")
        time.sleep(1.5)
        
        # Reset to idle state after setup is complete
        self.app.set_recovery_state("idle", {"action": "setup_complete"})
        self.update_heartbeat()  # Final heartbeat update
        print("✅ Initial setup complete")
    
    def process_post_catch_workflow(self):
        """Complete post-catch workflow: search for drops, find text, log to webhook and dev mode"""
        print("🎣 Processing post-catch workflow...")
        
        # Step 1: Switch to drop layout for text recognition
        original_layout = self.app.layout_manager.current_layout
        if original_layout != 'drop':
            print("📍 Switching to drop layout for text recognition...")
            self.app.layout_manager.toggle_layout()
            if hasattr(self.app, 'overlay_manager'):
                self.app.overlay_manager.update_layout()
        
        # Step 2: Search for drops and extract text
        drop_info = self.search_for_drops()
        
        # Step 3: Store fruit if enabled AND we actually caught a fruit
        if drop_info and drop_info.get('has_fruit', False):
            print("🍎 Fruit detected in catch - running fruit storage sequence")
            
            # Send webhook notification for devil fruit
            if (hasattr(self.app, 'webhook_manager') and 
                getattr(self.app, 'devil_fruit_webhook_enabled', True)):
                self.app.webhook_manager.send_devil_fruit_drop(drop_info)
            
            self.store_fruit()
        elif getattr(self.app, 'fruit_storage_enabled', False):
            print("⏭️ No fruit detected - skipping fruit storage sequence")
        else:
            print("⏭️ Fruit storage disabled - skipping sequence")
        
        # Step 4: Switch back to bar layout if needed
        if original_layout != 'drop':
            print("📍 Switching back to bar layout...")
            self.app.layout_manager.toggle_layout()
            if hasattr(self.app, 'overlay_manager'):
                self.app.overlay_manager.update_layout()
        
        print("✅ Post-catch workflow complete")
    
    def check_legendary_pity(self, drop_text):
        """
        Check if devil fruit drop is legendary by detecting pity counters
        Legendary drops show: 0/37, 0/40, 0/92, 0/100
        Non-legendary show: 1/37, 2/40, etc.
        """
        import re
        
        # Look for pity counter patterns (0/X means legendary drop occurred)
        pity_patterns = []
        # Generate patterns for 0/1 through 0/100
        for i in range(1, 101):
            pity_patterns.append(f'0/{i}')
        
        # Convert to regex patterns
        pity_patterns = [re.escape(pattern) for pattern in pity_patterns]
        
        text_lower = drop_text.lower()
        
        # Check for legendary indicators (only "legendary" keyword, not "pity")
        legendary_keywords = ['legendary']
        has_legendary_keyword = any(keyword in text_lower for keyword in legendary_keywords)
        
        # Check for pity counter patterns (only 0/X means legendary)
        has_legendary_pity = any(re.search(pattern, drop_text) for pattern in pity_patterns)
        
        # Must have either legendary keyword OR legendary pity counter (0/X)
        is_legendary = has_legendary_keyword or has_legendary_pity
        
        if is_legendary:
            print(f"🔍 Legendary detection: keyword={has_legendary_keyword}, pity={has_legendary_pity}")
            print(f"📝 Drop text: {drop_text}")
        
        return is_legendary

    def search_for_drops(self):
        """Search for drops in the drop layout area and extract text"""
        drop_info = {'has_fruit': False, 'drop_text': '', 'is_legendary': False}
        
        try:
            # Only process if OCR is available
            if not hasattr(self.app, 'ocr_manager') or not self.app.ocr_manager.get_stats()['available']:
                print("📝 OCR not available, skipping drop search")
                return drop_info
            
            # Get drop layout area
            drop_area = self.app.layout_manager.get_layout_area('drop')
            if not drop_area:
                print("📝 No drop area configured, skipping drop search")
                return drop_info
            
            print("🔍 Searching for drops in drop area...")
            
            # Capture screenshot of drop area
            import mss
            with mss.mss() as sct:
                monitor = {
                    'left': drop_area['x'],
                    'top': drop_area['y'],
                    'width': drop_area['width'],
                    'height': drop_area['height']
                }
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                # Convert BGRA to BGR (remove alpha channel if present)
                if img.shape[2] == 4:
                    img = img[:, :, :3]
            
            # Extract text using OCR from drop layout area
            if hasattr(self.app, 'ocr_manager'):
                drop_text = self.app.ocr_manager.extract_text()  # No screenshot_area needed - uses drop layout
                if drop_text:
                    drop_info['drop_text'] = drop_text
                    
                    if drop_text == "TEXT_DETECTED_NO_OCR":
                        print("📝 Text-like content detected in drop area (install Tesseract OCR for full text recognition)")
                        # Assume it might be a fruit since we can't read it
                        drop_info['has_fruit'] = True
                    else:
                        print(f"📝 Drop detected: {drop_text}")
                        
                        # Check if it's a devil fruit (One Piece game specific)
                        devil_fruit_keywords = ['devil', 'fruit', 'backpack', 'drop', 'got', 'fished up']
                        drop_text_lower = drop_text.lower()
                        
                        # Look for devil fruit related phrases
                        devil_fruit_phrases = [
                            'devil fruit',
                            'fished up a devil',
                            'got a devil fruit',
                            'devil fruit drop',
                            'check your backpack'
                        ]
                        
                        # Check for specific phrases first
                        for phrase in devil_fruit_phrases:
                            if phrase in drop_text_lower:
                                drop_info['has_fruit'] = True
                                print(f"🍎 Devil fruit detected in drop: '{phrase}'")
                                break
                        
                        # If no phrase match, check for individual keywords (need at least 2)
                        if not drop_info['has_fruit']:
                            keyword_matches = sum(1 for keyword in devil_fruit_keywords if keyword in drop_text_lower)
                            if keyword_matches >= 2:
                                drop_info['has_fruit'] = True
                                print(f"🍎 Devil fruit detected (keyword match count: {keyword_matches})")
                        
                        # Check for devil fruit drops
                        if 'devil fruit' in drop_text_lower:
                            drop_info['has_fruit'] = True
                            print(f"🍎 Devil fruit detected!")
                        
                        # Check for devil fruit spawn notifications
                        fruit_name = self.app.ocr_manager.detect_fruit_spawn(drop_text)
                        if fruit_name:
                            print(f"🌟 Devil fruit spawn detected: {fruit_name}")
                            # Send webhook notification
                            if hasattr(self.app, 'webhook_manager'):
                                self.app.webhook_manager.send_fruit_spawn(fruit_name)
                        
                        # Display in drop overlay
                        if hasattr(self.app, 'overlay_manager_drop') and self.app.overlay_manager_drop.window:
                            self.app.overlay_manager_drop.display_captured_text(drop_text)
                        
                        # Log to dev mode (console)
                        if getattr(self.app, 'dev_mode', False):
                            print(f"🔧 [DEV MODE] Drop details: {drop_text}")
                        
                else:
                    print("📝 No text found in drop area")
                        
        except Exception as e:
            print(f"❌ Drop search error: {e}")
        
        return drop_info
    
    def process_auto_zoom(self):
        """Process automatic zoom control (DISABLED - handled in perform_initial_setup)"""
        # This method is disabled to prevent conflicts with the main zoom sequence
        # Auto zoom is now handled in perform_initial_setup() only
        return