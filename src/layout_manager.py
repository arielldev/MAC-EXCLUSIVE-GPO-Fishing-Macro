"""
Layout Manager for Dual Overlay System
Handles switching between Bar Layout (blue) and Drop Layout (green)
"""

import json
import os

class LayoutManager:
    def __init__(self, app):
        self.app = app
        self.current_layout = "bar"  # "bar" or "drop"
        
        # Layout configurations
        self.layouts = {
            "bar": {
                "name": "BAR LAYOUT",
                "color": (85, 170, 255),  # Blue
                "border_color": (0, 100, 200),
                "area": None,  # Will be set by user
                "description": "Fishing Bar Detection"
            },
            "drop": {
                "name": "DROP LAYOUT", 
                "color": (85, 255, 85),   # Green
                "border_color": (0, 200, 0),
                "area": None,  # Will be set by user
                "description": "Loot Drop Recognition"
            }
        }
        
        # Load saved layout areas
        self.load_layout_settings()
    
    def get_current_layout(self):
        """Get current layout configuration"""
        return self.layouts[self.current_layout]
    
    def get_layout_name(self):
        """Get current layout display name"""
        return self.layouts[self.current_layout]["name"]
    
    def get_layout_color(self):
        """Get current layout color"""
        return self.layouts[self.current_layout]["color"]
    
    def get_border_color(self):
        """Get current layout border color"""
        return self.layouts[self.current_layout]["border_color"]
    
    def toggle_layout(self):
        """Toggle between bar and drop layouts"""
        old_layout = self.current_layout
        self.current_layout = "drop" if self.current_layout == "bar" else "bar"
        
        print(f"🔄 Layout switched: {self.layouts[old_layout]['name']} → {self.layouts[self.current_layout]['name']}")
        
        # Save current layout preference
        self.save_layout_settings()
        
        return self.current_layout
    
    def set_layout_area(self, layout_name, area):
        """Set area for specific layout"""
        if layout_name in self.layouts:
            self.layouts[layout_name]["area"] = area
            self.save_layout_settings()
            print(f"📍 {self.layouts[layout_name]['name']} area saved: {area}")
    
    def get_layout_area(self, layout_name=None):
        """Get area for specific layout (or current if None)"""
        layout_name = layout_name or self.current_layout
        return self.layouts[layout_name]["area"]
    
    def has_layout_area(self, layout_name=None):
        """Check if layout has configured area"""
        layout_name = layout_name or self.current_layout
        area = self.layouts[layout_name]["area"]
        return area is not None and all(key in area for key in ['x', 'y', 'width', 'height'])
    
    def load_layout_settings(self):
        """Load layout settings from file"""
        try:
            settings_file = "layout_settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                
                # Load current layout
                self.current_layout = data.get("current_layout", "bar")
                
                # Load layout areas
                for layout_name in ["bar", "drop"]:
                    if layout_name in data.get("layout_areas", {}):
                        self.layouts[layout_name]["area"] = data["layout_areas"][layout_name]
                
                print(f"✅ Layout settings loaded - Current: {self.get_layout_name()}")
        
        except Exception as e:
            print(f"⚠️ Could not load layout settings: {e}")
    
    def save_layout_settings(self):
        """Save layout settings to file"""
        try:
            settings_data = {
                "current_layout": self.current_layout,
                "layout_areas": {
                    "bar": self.layouts["bar"]["area"],
                    "drop": self.layouts["drop"]["area"]
                }
            }
            
            with open("layout_settings.json", 'w') as f:
                json.dump(settings_data, f, indent=2)
            
        except Exception as e:
            print(f"⚠️ Could not save layout settings: {e}")
    
    def get_layout_info(self):
        """Get formatted layout information for display"""
        current = self.get_current_layout()
        return {
            "name": current["name"],
            "description": current["description"],
            "color": current["color"],
            "has_area": self.has_layout_area()
        }