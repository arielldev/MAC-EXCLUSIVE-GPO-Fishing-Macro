import tkinter as tk
import sys
import os

# Add the src directory to the path for imports
if hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle
    sys.path.insert(0, sys._MEIPASS)
else:
    # Running as script
    sys.path.insert(0, os.path.dirname(__file__))

from gui import HotkeyGUI

def main():
    root = tk.Tk()
    
    
    # Set window icon
    try:
        from PIL import Image, ImageTk
        import os
        
        # Handle icon path for both development and PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            icon_path = os.path.join(sys._MEIPASS, "images", "icon.webp")
        else:
            # Running as script
            icon_path = os.path.join(os.path.dirname(__file__), "..", "images", "icon.webp")
            
        if os.path.exists(icon_path):
            icon_image = Image.open(icon_path)
            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(icon_image)
            root.iconphoto(True, photo)
        else:
            print(f"Icon not found at: {icon_path}")
    except Exception as e:
        print(f"Could not load icon: {e}")
    
    app = HotkeyGUI(root)
    root.protocol('WM_DELETE_WINDOW', app.exit_app)
    root.mainloop()

if __name__ == '__main__':
    main()
