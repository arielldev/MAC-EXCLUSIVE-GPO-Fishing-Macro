import tkinter as tk
from tkinter import ttk

class OverlayManager:
    def __init__(self, app, fixed_layout=None):
        self.app = app
        self.fixed_layout = fixed_layout  # If set, always use this layout instead of current
        self.window = None
        self.frame = None
        self.label = None
        self.drag_data = {'x': 0, 'y': 0, 'resize_edge': None, 'start_width': 0, 
                         'start_height': 0, 'start_x': 0, 'start_y': 0}
    
    def create(self):
        if self.window is not None:
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.overrideredirect(True)
        self.window.attributes('-alpha', 0.6)
        self.window.attributes('-topmost', True)
        self.window.minsize(1, 1)
        
        # Get current layout area
        current_area = self.get_current_area()
        x = current_area['x']
        y = current_area['y']
        width = current_area['width']
        height = current_area['height']
        geometry = f"{width}x{height}+{x}+{y}"
        self.window.geometry(geometry)
        
        # Create frame with layout-specific colors
        current_layout = self.get_current_layout()
        layout_config = self.app.layout_manager.layouts[current_layout]
        bg_color = self._rgb_to_hex(layout_config['color'])
        border_color = self._rgb_to_hex(layout_config['border_color'])
        
        self.frame = tk.Frame(self.window, bg=bg_color, highlightthickness=3, 
                             highlightbackground=border_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Add layout label overlaid on the content (no separate header space)
        self.label = tk.Label(self.frame, text=layout_config['name'], 
                             bg=bg_color, fg='white', font=('Arial', 12, 'bold'))
        # Center the label at the top
        self.label.place(relx=0.5, y=5, anchor='n')
        
        # Add text display area for OCR results (only for drop layout)
        self.text_display = None
        current_layout = self.get_current_layout()
        if current_layout == 'drop':
            # Create text display with transparent background matching the overlay style
            self.text_display = tk.Text(self.frame, height=4, width=30, 
                                      bg=bg_color, fg='white', font=('Courier', 9),
                                      wrap=tk.WORD, state=tk.DISABLED, bd=0, 
                                      highlightthickness=0, relief='flat')
            # Position it below the title with some padding
            self.text_display.pack(pady=(30, 5), padx=5, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.window.bind("<ButtonPress-1>", self._start_action)
        self.window.bind("<B1-Motion>", self._motion)
        self.window.bind("<Motion>", self._update_cursor)
        self.window.bind("<Configure>", self._on_configure)
        
        self.frame.bind("<ButtonPress-1>", self._start_action)
        self.frame.bind("<B1-Motion>", self._motion)
        self.frame.bind("<Motion>", self._update_cursor)
        
        # Bind mouse events to label as well
        self.label.bind("<ButtonPress-1>", self._start_action)
        self.label.bind("<B1-Motion>", self._motion)
        self.label.bind("<Motion>", self._update_cursor)
    
    def destroy(self):
        if self.window is not None:
            # Save area to the correct layout
            current_layout = self.get_current_layout()
            area = {
                'x': self.window.winfo_x(),
                'y': self.window.winfo_y(),
                'width': self.window.winfo_width(),
                'height': self.window.winfo_height()
            }
            self.app.layout_manager.set_layout_area(current_layout, area)
            
            self.window.destroy()
            self.window = None
            self.frame = None
            self.label = None
    
    def _get_resize_edge(self, x, y):
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        edge_size = 10
        on_left = x < edge_size
        on_right = x > width - edge_size
        on_top = y < edge_size
        on_bottom = y > height - edge_size
        
        if on_top and on_left:
            return "nw"
        elif on_top and on_right:
            return "ne"
        elif on_bottom and on_left:
            return "sw"
        elif on_bottom and on_right:
            return "se"
        elif on_left:
            return "w"
        elif on_right:
            return "e"
        elif on_top:
            return "n"
        elif on_bottom:
            return "s"
        return None
    
    def _update_cursor(self, event):
        edge = self._get_resize_edge(event.x, event.y)
        cursor_map = {'nw': 'size_nw_se', 'ne': 'size_ne_sw', 'sw': 'size_ne_sw', 
                     'se': 'size_nw_se', 'n': 'size_ns', 's': 'size_ns', 
                     'e': 'size_we', 'w': 'size_we', None: 'arrow'}
        self.window.config(cursor=cursor_map.get(edge, 'arrow'))
    
    def _start_action(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.drag_data['resize_edge'] = self._get_resize_edge(event.x, event.y)
        self.drag_data['start_width'] = self.window.winfo_width()
        self.drag_data['start_height'] = self.window.winfo_height()
        self.drag_data['start_x'] = self.window.winfo_x()
        self.drag_data['start_y'] = self.window.winfo_y()
    
    def _motion(self, event):
        edge = self.drag_data['resize_edge']
        
        if edge is None:
            x = self.window.winfo_x() + event.x - self.drag_data['x']
            y = self.window.winfo_y() + event.y - self.drag_data['y']
            self.window.geometry(f'+{x}+{y}')
        else:
            dx = event.x - self.drag_data['x']
            dy = event.y - self.drag_data['y']
            
            new_width = self.drag_data['start_width']
            new_height = self.drag_data['start_height']
            new_x = self.drag_data['start_x']
            new_y = self.drag_data['start_y']
            
            if 'e' in edge:
                new_width = max(1, self.drag_data['start_width'] + dx)
            elif 'w' in edge:
                new_width = max(1, self.drag_data['start_width'] - dx)
                new_x = self.drag_data['start_x'] + dx
            
            if 's' in edge:
                new_height = max(1, self.drag_data['start_height'] + dy)
            elif 'n' in edge:
                new_height = max(1, self.drag_data['start_height'] - dy)
                new_y = self.drag_data['start_y'] + dy
            
            self.window.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
    
    def _on_configure(self, event=None):
        if self.window is not None:
            # Update area for the correct layout
            current_layout = self.get_current_layout()
            area = {
                'x': self.window.winfo_x(),
                'y': self.window.winfo_y(),
                'width': self.window.winfo_width(),
                'height': self.window.winfo_height()
            }
            self.app.layout_manager.set_layout_area(current_layout, area)

    
    def get_current_layout(self):
        """Get the layout this overlay should use"""
        return self.fixed_layout or self.app.layout_manager.current_layout
    
    def get_current_area(self):
        """Get area for current layout"""
        current_layout = self.get_current_layout()
        area = self.app.layout_manager.get_layout_area(current_layout)
        
        # Provide layout-specific defaults if no area set
        if not area:
            if current_layout == 'bar':
                # Default bar layout area (fishing bar position)
                area = {'x': 700, 'y': 400, 'width': 200, 'height': 100}
            elif current_layout == 'drop':
                # Default drop layout area (loot drop position)  
                area = {'x': 800, 'y': 200, 'width': 300, 'height': 400}
            else:
                # Fallback to legacy overlay_area
                area = getattr(self.app, 'overlay_area', {'x': 100, 'y': 100, 'width': 200, 'height': 100}).copy()
        
        return area
    
    def update_layout(self):
        """Update overlay appearance for current layout"""
        if self.window is None:
            return
        
        current_layout = self.get_current_layout()
        layout_config = self.app.layout_manager.layouts[current_layout]
        
        # Update colors
        bg_color = self._rgb_to_hex(layout_config['color'])
        border_color = self._rgb_to_hex(layout_config['border_color'])
        
        if self.frame:
            self.frame.config(bg=bg_color, highlightbackground=border_color)
        
        if self.label:
            self.label.config(text=layout_config['name'], bg=bg_color)
            # Ensure label is properly positioned and visible
            self.label.place(relx=0.5, y=5, anchor='n')
        
        # Add or remove text display based on layout
        if current_layout == 'drop' and not self.text_display:
            # Create text display with transparent background matching the overlay style
            self.text_display = tk.Text(self.frame, height=4, width=30, 
                                      bg=bg_color, fg='white', font=('Courier', 9),
                                      wrap=tk.WORD, state=tk.DISABLED, bd=0, 
                                      highlightthickness=0, relief='flat')
            # Position it below the title with some padding
            self.text_display.pack(pady=(30, 5), padx=5, fill=tk.BOTH, expand=True)
        elif current_layout == 'bar' and self.text_display:
            self.text_display.destroy()
            self.text_display = None
        
        # Update text display colors if it exists
        if self.text_display and current_layout == 'drop':
            self.text_display.config(bg=bg_color, fg='white')
        
        # Update position to current layout area
        current_area = self.get_current_area()
        geometry = f"{current_area['width']}x{current_area['height']}+{current_area['x']}+{current_area['y']}"
        self.window.geometry(geometry)
        
        print(f"🎯 Overlay updated for {layout_config['name']}")
    
    def display_captured_text(self, text):
        """Display captured OCR text in the overlay"""
        if self.text_display and text:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            
            # Add timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.text_display.insert(tk.END, f"[{timestamp}]\n", "timestamp")
            self.text_display.insert(tk.END, text + "\n\n")
            
            # Scroll to bottom
            self.text_display.see(tk.END)
            self.text_display.config(state=tk.DISABLED)
    
    def clear_text_display(self):
        """Clear the text display area"""
        if self.text_display:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.config(state=tk.DISABLED)
    
    def _rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
