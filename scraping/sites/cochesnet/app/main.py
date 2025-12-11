"""
Entry point for Cochesnet desktop scraper application.

This provides a graphical interface for scraping Coches.net by year.

Usage:
    python scraping/sites/cochesnet/app/main.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.cochesnet.app.gui import main


if __name__ == "__main__":
    print("="*60)
    print("COCHESNET DESKTOP SCRAPER")
    print("="*60)
    print("\nStarting GUI application...")
    print("Select years (2007-2025) to scrape")
    print("\nClose this window when done.\n")

    main()
