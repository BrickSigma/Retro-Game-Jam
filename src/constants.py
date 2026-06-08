"""
Module containing all global variables, constants, and other utilities.
"""

import sys
import os

def resource_path(relative_path: str) -> str:
    """Resolve a path to a bundled asset — works in dev and as a PyInstaller exe."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

SCREEN_SIZE = (256, 240)  # Screen resolution
SCALE = 3                 # Scale to apply to screen for bigger displays

WINDOW_SIZE = (SCREEN_SIZE[0]*SCALE, SCREEN_SIZE[1]*SCALE)  # Size of the actual window

FPS = 60    # Frame rate
