from datetime import datetime

class WebhookManager:
    def __init__(self, app):
        self.app = app
        self.devil_fruit_count = 0  # Track devil fruits caught
    
    def send_fishing_progress(self):
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if fish progress notifications are enabled
        if not getattr(self.app, 'fish_progress_webhook_enabled', True):
            return
            
        try:
            import requests
            
            embed = {
                "title": "🎣 GPO Autofish Progress",
                "description": f"Successfully caught **{self.app.webhook_interval}** fish!",
                "color": 0x00ff00,
                "fields": [
                    {"name": "🐟 Total Fish Caught", "value": str(self.app.fish_count), "inline": True},
                    {"name": "⏱️ Session Progress", "value": f"{self.app.webhook_interval} fish in last interval", "inline": True}
                ],
                "footer": {"text": "GPO Autofish - Open Source"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Webhook sent: {self.app.webhook_interval} fish caught!")
            else:
                print(f"❌ Webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Webhook error: {e}")

    def send_fruit_spawn(self, fruit_name):
        """Send webhook notification for devil fruit spawns"""
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if spawn notifications are enabled
        if not getattr(self.app, 'fruit_spawn_webhook_enabled', True):
            return
            
        try:
            import requests
            
            embed = {
                "title": "🌟 Devil Fruit Spawned!",
                "description": f"A **{fruit_name}** devil fruit has spawned in the world!",
                "color": 0xFFD700,  # Gold color for spawn
                "fields": [
                    {"name": "🍎 Fruit", "value": fruit_name, "inline": True},
                    {"name": "⏰ Time", "value": datetime.now().strftime("%H:%M:%S"), "inline": True}
                ],
                "footer": {"text": "GPO Autofish - Fruit Spawn Alert"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"🌟 Fruit spawn webhook sent: {fruit_name}")
            else:
                print(f"❌ Fruit spawn webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Fruit spawn webhook error: {e}")
    
    def send_devil_fruit_drop(self, drop_info=None):
        """Send webhook notification for devil fruit drops"""
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if devil fruit notifications are enabled
        if not getattr(self.app, 'devil_fruit_webhook_enabled', True):
            return
            
        # Increment devil fruit counter
        self.devil_fruit_count += 1
            
        try:
            import requests
            
            # Build description with OCR text if available
            description = "Devil fruit detected and stored!"
            if drop_info and drop_info.get('ocr_text'):
                # Clean up the OCR text for display
                ocr_text = drop_info['ocr_text'][:100]  # Limit length
                description += f"\n\n**OCR Text:** {ocr_text}"
            
            embed = {
                "title": "🍎 Devil Fruit Caught!",
                "description": description,
                "color": 0x9c27b0,  # Purple color for devil fruit
                "fields": [
                    {"name": "🍎 Devil Fruits", "value": str(self.devil_fruit_count), "inline": True},
                    {"name": "🐟 Total Fish Caught", "value": str(self.app.fish_count), "inline": True},
                    {"name": "⏰ Time", "value": datetime.now().strftime("%H:%M:%S"), "inline": True}
                ],
                "footer": {"text": "GPO Autofish - Devil Fruit Caught!"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add detection confidence if available
            if drop_info and drop_info.get('keyword_matches'):
                embed["fields"].append({
                    "name": "🎯 Detection", 
                    "value": f"{drop_info['keyword_matches']} keyword matches", 
                    "inline": True
                })
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"🍎 Devil fruit webhook sent! Total: {self.devil_fruit_count}")
            else:
                print(f"❌ Devil fruit webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Devil fruit webhook error: {e}")
    

    
    def send_purchase(self, amount):
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if purchase notifications are enabled
        if not getattr(self.app, 'purchase_webhook_enabled', True):
            return
            
        try:
            import requests
            
            embed = {
                "title": "🛒 GPO Autofish - Auto Purchase",
                "description": f"Successfully purchased **{amount}** bait!",
                "color": 0xffa500,
                "fields": [
                    {"name": "🎣 Bait Purchased", "value": str(amount), "inline": True},
                    {"name": "🐟 Total Fish Caught", "value": str(self.app.fish_count), "inline": True},
                    {"name": "🔄 Status", "value": "Auto purchase completed successfully", "inline": False}
                ],
                "footer": {"text": "GPO Autofish - Auto Purchase System"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Purchase webhook sent: Bought {amount} bait!")
            else:
                print(f"❌ Purchase webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Purchase webhook error: {e}")
    
    def send_bait_depleted(self, bait_type, remaining_quantities):
        """Send webhook notification when bait runs out"""
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if bait notifications are enabled
        if not getattr(self.app, 'bait_webhook_enabled', True):
            return
            
        try:
            import requests
            
            # Create quantities display
            qty_display = []
            for bait, qty in remaining_quantities.items():
                qty_display.append(f"{bait.title()}: {qty}")
            
            embed = {
                "title": "🎣 Bait Depleted!",
                "description": f"**{bait_type.title()}** bait has run out!",
                "color": 0xff6b35,  # Orange-red color for warning
                "fields": [
                    {"name": "🚨 Depleted Bait", "value": bait_type.title(), "inline": True},
                    {"name": "📊 Remaining Bait", "value": "\n".join(qty_display), "inline": True},
                    {"name": "🐟 Fish Caught", "value": str(self.app.fish_count), "inline": True}
                ],
                "footer": {"text": "GPO Autofish - Bait Management"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"🎣 Bait depletion webhook sent: {bait_type} bait depleted!")
            else:
                print(f"❌ Bait depletion webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Bait depletion webhook error: {e}")
    
    def send_auto_purchase_triggered(self, reason, purchase_amount):
        """Send webhook notification when auto purchase is triggered by bait system"""
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if bait notifications are enabled
        if not getattr(self.app, 'bait_webhook_enabled', True):
            return
            
        try:
            import requests
            
            embed = {
                "title": "🛒 Auto Purchase Triggered",
                "description": f"Auto purchase activated: {reason}",
                "color": 0x4caf50,  # Green color for action
                "fields": [
                    {"name": "🎯 Trigger Reason", "value": reason, "inline": True},
                    {"name": "🛒 Purchase Amount", "value": str(purchase_amount), "inline": True},
                    {"name": "🐟 Fish Caught", "value": str(self.app.fish_count), "inline": True},
                    {"name": "📈 Status", "value": "Purchasing common bait automatically", "inline": False}
                ],
                "footer": {"text": "GPO Autofish - Auto Purchase System"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"🛒 Auto purchase trigger webhook sent: {reason}")
            else:
                print(f"❌ Auto purchase trigger webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Auto purchase trigger webhook error: {e}")

    def send_recovery(self, recovery_info):
        if not self.app.webhook_url or not self.app.webhook_enabled:
            return
        
        # Check if recovery notifications are enabled
        if not getattr(self.app, 'recovery_webhook_enabled', True):
            return
            
        try:
            import requests
            
            if recovery_info["recovery_number"] == 1:
                color = 0xffff00
            elif recovery_info["recovery_number"] <= 3:
                color = 0xffa500
            else:
                color = 0xff0000
            
            embed = {
                "title": "🔄 GPO Autofish - Recovery Triggered",
                "description": f"Recovery #{recovery_info['recovery_number']} - System detected stuck state",
                "color": color,
                "fields": [
                    {"name": "🚨 Stuck Action", "value": recovery_info["stuck_state"], "inline": True},
                    {"name": "⏱️ Stuck Duration", "value": f"{recovery_info['stuck_duration']:.1f}s", "inline": True},
                    {"name": "🔢 Recovery Count", "value": str(recovery_info["recovery_number"]), "inline": True},
                    {"name": "🐟 Fish Caught", "value": str(self.app.fish_count), "inline": True},
                    {"name": "📊 Status", "value": "System automatically restarted", "inline": False}
                ],
                "footer": {"text": "GPO Autofish - Recovery"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if (self.app.dev_mode or self.app.verbose_logging) and recovery_info.get("state_details"):
                embed["fields"].append({
                    "name": "🔍 Dev Details",
                    "value": str(recovery_info["state_details"])[:1000],
                    "inline": False
                })
            
            payload = {"embeds": [embed], "username": "GPO Autofish Recovery Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Recovery webhook sent: Recovery #{recovery_info['recovery_number']}")
            else:
                print(f"❌ Recovery webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Recovery webhook error: {e}")
    
    def test(self):
        if not self.app.webhook_url:
            print("❌ Please enter a webhook URL first")
            return
            
        try:
            import requests
            
            embed = {
                "title": "🧪 GPO Autofish Test",
                "description": "Webhook test successful! ✅",
                "color": 0x0099ff,
                "fields": [{"name": "🔧 Status", "value": "Webhook is working correctly", "inline": True}],
                "footer": {"text": "GPO Autofish - Open Source"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed], "username": "GPO Autofish Bot"}
            response = requests.post(self.app.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print("✅ Test webhook sent successfully!")
            else:
                print(f"❌ Test webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test webhook error: {e}")
