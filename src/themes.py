import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class ThemeManager:
    def __init__(self, app):
        self.app = app
        self.themes = {
        "default": {
    "name": "Default",
    "description": "Dark red theme with bold, modern styling",
    "colors": {
        "bg": "#160003",
        "fg": "#ffdddd",
        "accent": "#ff4d4d",
        "success": "#7edc92",
        "error": "#ff3b3b",
        "warning": "#ff9966",
        "button_bg": "#2a0004",
        "button_hover": "#3a0006",
        "scrollbar_bg": "#2a0004",
        "scrollbar_trough": "#160003",
        "scrollbar_active": "#3a0006",
        "scrollbar_pressed": "#55000a"
    }
},

            "dark": {
                "name": "Dark Mode",
                "description": "Pure black theme with gray accents for maximum darkness",
                "colors": {
                    "bg": "#000000",
                    "fg": "#e0e0e0",
                    "accent": "#808080",
                    "success": "#4caf50",
                    "error": "#f44336",
                    "warning": "#ff9800",
                    "button_bg": "#1a1a1a",
                    "button_hover": "#2a2a2a",
                    "scrollbar_bg": "#1a1a1a",
                    "scrollbar_trough": "#000000",
                    "scrollbar_active": "#2a2a2a",
                    "scrollbar_pressed": "#3a3a3a"
                }
            },
     "pink": {
    "name": "Pink Theme",
    "description": "Light, cute pink theme with soft pastel vibes",
    "colors": {
        "bg": "#ffeef7",
        "fg": "#4a2e3f",
        "accent": "#ff9acb",
        "success": "#b6f2c7",
        "error": "#ff6fa3",
        "warning": "#ffb78c",
        "button_bg": "#ffd6e9",
        "button_hover": "#ffc2e1",
        "scrollbar_bg": "#ffd6e9",
        "scrollbar_trough": "#ffeef7",
        "scrollbar_active": "#ffc2e1",
        "scrollbar_pressed": "#ffadd6"
    }
},
            "christmas": {
                "name": "Christmas Theme",
                "description": "Festive white, red and green theme for the holidays",
                "colors": {
                    "bg": "#ffffff",
                    "fg": "#2d1b1b",
                    "accent": "#dc143c",
                    "success": "#228b22",
                    "error": "#b22222",
                    "warning": "#ff8c00",
                    "button_bg": "#f0fff0",
                    "button_hover": "#e8f5e8",
                    "scrollbar_bg": "#f0fff0",
                    "scrollbar_trough": "#ffffff",
                    "scrollbar_active": "#e8f5e8",
                    "scrollbar_pressed": "#d0f0d0"
                }
            },
            "ocean": {
                "name": "Ocean Theme",
                "description": "Cool ocean blues and aqua tones",
                "colors": {
                    "bg": "#0f1419",
                    "fg": "#e6fffa",
                    "accent": "#00bcd4",
                    "success": "#4caf50",
                    "error": "#f44336",
                    "warning": "#ff9800",
                    "button_bg": "#1e2a2e",
                    "button_hover": "#2e3a3e",
                    "scrollbar_bg": "#1e2a2e",
                    "scrollbar_trough": "#0f1419",
                    "scrollbar_active": "#2e3a3e",
                    "scrollbar_pressed": "#3e4a4e"
                }
            },
        "sunset": {
    "name": "Sunset Theme",
    "description": "Soft glowing sunset with warm oranges and dreamy purples",
    "colors": {
        "bg": "#3b1f3a",
        "fg": "#ffe9d9",
        "accent": "#ff8a4f",
        "success": "#a5e38a",
        "error": "#ff4f7b",
        "warning": "#ffca73",
        "button_bg": "#4b2947",
        "button_hover": "#5a3256",
        "scrollbar_bg": "#4b2947",
        "scrollbar_trough": "#3b1f3a",
        "scrollbar_active": "#5a3256",
        "scrollbar_pressed": "#6a3966"
    }
},


"purple": {
    "name": "Purple Theme",
    "description": "Deep royal purple with soft, modern highlights",
    "colors": {
        "bg": "#241433",
        "fg": "#efe6ff",
        "accent": "#b05cff",
        "success": "#7edc92",
        "error": "#ff4e63",
        "warning": "#ffbb66",
        "button_bg": "#332046",
        "button_hover": "#402a58",
        "scrollbar_bg": "#332046",
        "scrollbar_trough": "#241433",
        "scrollbar_active": "#402a58",
        "scrollbar_pressed": "#503068"
    }
},

            "neon": {
                "name": "Neon Theme",
                "description": "Bright neon colors for vibrant experience",
                "colors": {
                    "bg": "#0a0a0a",
                    "fg": "#ffffff",
                    "accent": "#00ff41",
                    "success": "#39ff14",
                    "error": "#ff073a",
                    "warning": "#ffff00",
                    "button_bg": "#1a1a1a",
                    "button_hover": "#2a2a2a",
                    "scrollbar_bg": "#1a1a1a",
                    "scrollbar_trough": "#0a0a0a",
                    "scrollbar_active": "#2a2a2a",
                    "scrollbar_pressed": "#3a3a3a"
                }
            }
        }
    
    def open_theme_window(self):
        """Open the modern theme selection window"""
        if hasattr(self.app, 'theme_window') and self.app.theme_window:
            self.app.theme_window.lift()
            return
        
        self.app.theme_window = tk.Toplevel(self.app.root)
        self.app.theme_window.title("🎨 Theme Selection")
        self.app.theme_window.geometry("600x450")
        self.app.theme_window.resizable(False, False)
        self.app.theme_window.transient(self.app.root)
        self.app.theme_window.grab_set()
        
        # Center the window
        self.app.theme_window.update_idletasks()
        x = (self.app.theme_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.app.theme_window.winfo_screenheight() // 2) - (450 // 2)
        self.app.theme_window.geometry(f"600x450+{x}+{y}")
        
        # Always use default theme colors for the theme window itself to avoid conflicts
        window_colors = self.themes["default"]["colors"]
        self.app.theme_window.configure(bg=window_colors["bg"])
        
        # Modern header with gradient-like effect
        header_frame = tk.Frame(self.app.theme_window, bg=window_colors["bg"], height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Title with better styling
        title_label = tk.Label(
            header_frame,
            text="🎨 Choose Your Theme",
            font=("Segoe UI", 24, "bold"),
            bg=window_colors["bg"],
            fg=window_colors["accent"]
        )
        title_label.pack(expand=True)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Select a theme to customize your experience",
            font=("Segoe UI", 10),
            bg=window_colors["bg"],
            fg=window_colors["fg"]
        )
        subtitle_label.pack()
        
        # Main content area with modern grid layout
        content_frame = tk.Frame(self.app.theme_window, bg=window_colors["bg"])
        content_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Create theme cards in a grid layout
        row = 0
        col = 0
        for theme_key, theme_data in self.themes.items():
            self.create_modern_theme_card(content_frame, theme_key, theme_data, window_colors, row, col)
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        # No footer - window will auto-close when theme is applied
        
        # Handle window close
        self.app.theme_window.protocol("WM_DELETE_WINDOW", self.close_theme_window)
    
    def create_modern_theme_card(self, parent, theme_key, theme_data, window_colors, row, col):
        """Create a simple, working theme selection card"""
        theme_colors = theme_data["colors"]
        is_current = theme_key == self.app.current_theme
        
        # Main card container
        card_container = tk.Frame(parent, bg=window_colors["bg"])
        card_container.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        # Configure grid weights
        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)
        
        # Card frame - SAME for ALL themes
        card_frame = tk.Frame(
            card_container,
            bg=window_colors["button_bg"],
            relief="solid",
            bd=2 if is_current else 1
        )
        card_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Theme name at top
        name_label = tk.Label(
            card_frame,
            text=theme_data["name"],
            font=("Segoe UI", 16, "bold"),
            bg=window_colors["button_bg"],
            fg=window_colors["accent"]
        )
        name_label.pack(pady=(15, 10))
        
        # Color preview section
        preview_frame = tk.Frame(card_frame, bg=window_colors["button_bg"])
        preview_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Show theme's actual background color
        color_preview = tk.Frame(
            preview_frame,
            bg=theme_colors["bg"],
            height=60,
            relief="solid",
            bd=1
        )
        color_preview.pack(fill="x")
        color_preview.pack_propagate(False)
        
        # Theme colors in preview - better text visibility
        if theme_colors["bg"] == "#ffffff":
            preview_text_color = theme_colors["fg"]  # Use dark text on white
        else:
            preview_text_color = theme_colors["accent"]  # Use accent on dark
            
        preview_text = tk.Label(
            color_preview,
            text=theme_data["name"],
            font=("Segoe UI", 12, "bold"),
            bg=theme_colors["bg"],
            fg=preview_text_color
        )
        preview_text.pack(expand=True)
        
        # Description
        desc_label = tk.Label(
            card_frame,
            text=theme_data["description"],
            font=("Segoe UI", 9),
            bg=window_colors["button_bg"],
            fg=window_colors["fg"],
            wraplength=200,
            justify="center"
        )
        desc_label.pack(padx=15, pady=(0, 15))
        
        # Action button
        if is_current:
            btn = tk.Button(
                card_frame,
                text="✓ Currently Used",
                font=("Segoe UI", 10, "bold"),
                bg="#888888",
                fg="#ffffff",
                state="disabled",
                relief="flat",
                padx=20,
                pady=8
            )
        else:
            btn = tk.Button(
                card_frame,
                text=f"Apply {theme_data['name']}",
                font=("Segoe UI", 10, "bold"),
                bg=theme_colors["accent"],
                fg="#ffffff",
                relief="flat",
                padx=20,
                pady=8,
                command=lambda: self.apply_theme_and_close(theme_key),
                cursor="hand2"
            )
        
        btn.pack(pady=(0, 15))
    
    def apply_theme_and_close(self, theme_key):
        """Apply theme and immediately close window"""
        if theme_key in self.themes:
            # Apply the theme
            self.app.current_theme = theme_key
            self.app.apply_theme()
            self.app.auto_save_settings()
            
            # Close window immediately - NO STATUS UPDATE
            if hasattr(self.app, 'theme_window') and self.app.theme_window:
                self.app.theme_window.destroy()
                self.app.theme_window = None
                
            print(f"Applied {self.themes[theme_key]['name']} and closed window")
    
    def apply_theme(self, theme_key):
        """Apply the selected theme"""
        print(f"Applying theme: {theme_key}")  # Debug print
        if theme_key in self.themes:
            self.app.current_theme = theme_key
            self.app.apply_theme()
            self.app.auto_save_settings()
            
            # Update status message
            theme_name = self.themes[theme_key]["name"]
            self.app.update_status(f'Applied {theme_name}', 'success', '🎨')
        else:
            print(f"Theme {theme_key} not found!")  # Debug print
    
    def lighten_color(self, color):
        """Lighten a hex color for hover effects"""
        try:
            # Remove # if present
            color = color.lstrip('#')
            # Convert to RGB
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # Lighten by 20%
            r = min(255, int(r * 1.2))
            g = min(255, int(g * 1.2))
            b = min(255, int(b * 1.2))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color  # Return original if conversion fails
    
    def close_theme_window(self):
        """Close the theme window"""
        if hasattr(self.app, 'theme_window') and self.app.theme_window:
            # Unbind mouse wheel events
            try:
                self.app.theme_window.unbind_all("<MouseWheel>")
            except:
                pass
            
            self.app.theme_window.destroy()
            self.app.theme_window = None
    
    def load_logo_for_theme(self, theme_key):
        """Load the logo for the theme - always use icon.webp"""
        import sys
        try:
            # Handle logo path for both development and PyInstaller bundle
            if hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller bundle
                logo_path = os.path.join(sys._MEIPASS, "images", "icon.webp")
            else:
                # Running as script
                logo_path = os.path.join("images", "icon.webp")
            
            if os.path.exists(logo_path):
                image = Image.open(logo_path)
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
            else:
                print(f"Logo not found at: {logo_path}")
        except Exception as e:
            print(f"Could not load logo for theme {theme_key}: {e}")
        
        return None
    
    def update_logo(self):
        """Update the logo in the main window based on current theme"""
        # Logo functionality disabled - using text title only
        pass