#!/usr/bin/env python3
"""
Auto Bait Manager for GPO Autofish
Handles intelligent bait selection and management
"""

import time
import logging
from typing import Optional, Dict, Tuple

try:
    import keyboard
    import mss
    import numpy as np
    BAIT_AVAILABLE = True
except ImportError:
    BAIT_AVAILABLE = False
    print("❌ Bait management requires keyboard, mss, and numpy")

class BaitManager:
    """Manages automatic bait selection - simplified to just select top bait"""
    
    def __init__(self, app=None):
        self.app = app
        self.available = BAIT_AVAILABLE
        
    def is_enabled(self) -> bool:
        """Check if auto bait is enabled and available"""
        return (self.available and 
                getattr(self.app, 'auto_bait_enabled', False) and
                hasattr(self.app, 'top_bait_coords') and
                self.app.top_bait_coords)
    
    def select_top_bait(self) -> bool:
        """Simply click the top bait position - no complex logic"""
        if not self.is_enabled():
            return False
            
        try:
            x, y = self.app.top_bait_coords
            print(f"🎣 Selecting top bait at ({x}, {y})")
            self.app._click_at((x, y))
            time.sleep(0.2)  # Brief pause after selection
            return True
        except Exception as e:
            logging.error(f"Failed to select top bait: {e}")
            return False
    
    def select_bait_before_cast(self) -> bool:
        """Select top bait before casting rod - called every time before rod throw"""
        if not self.is_enabled():
            return True  # Don't block fishing if disabled
            
        try:
            print("🎣 Selecting top bait before cast...")
            return self.select_top_bait()
        except Exception as e:
            logging.error(f"Failed to select bait before cast: {e}")
            return True  # Don't block fishing on error