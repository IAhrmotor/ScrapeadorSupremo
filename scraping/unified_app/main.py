"""
Unified Scraper Application - Entry Point

Run this script to launch the unified desktop application for managing
both Autocasion and Cochesnet scraping operations.

Usage:
    python scraping/unified_app/main.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import tkinter as tk
from tkinter import messagebox

from scraping.unified_app.gui import UnifiedScraperApp
from core.debug import get_debugger, DebugLevel

# Configure debug level
debug = get_debugger()
debug.set_level(DebugLevel.INFO)


def main():
    """Launch the unified scraper application."""
    try:
        # Create root window
        root = tk.Tk()

        # Create application
        app = UnifiedScraperApp(root)

        # Start mainloop
        root.mainloop()

    except Exception as e:
        error_msg = f"Failed to start application: {e}"
        print(error_msg)

        # Show error dialog if tkinter is available
        try:
            messagebox.showerror("Application Error", error_msg)
        except:
            pass

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
