"""Focus Guardian - ADHD Productivity Application

IMPORTANT: Run this as Administrator for blocking features to work!
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import json
import os
import sys
import subprocess
import ctypes
import datetime
import threading
import time
from pathlib import Path
import hashlib
from ui.app import FocusGuardian
import ui.app as ui_app

# Optional timezone support
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False
    print("Note: pytz not installed. Install with: pip install pytz")

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

ui_app.is_admin = is_admin
if __name__ == "__main__":
    root = tk.Tk()
    app = FocusGuardian(root)
    root.mainloop()
