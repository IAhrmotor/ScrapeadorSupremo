"""
Autocasion Desktop Application
==============================

Main entry point for the Autocasion scraper desktop application.

Usage:
    GUI Mode:  python main.py
    CLI Mode:  python main.py cli [command] [options]

CLI Commands:
    scrape --marcas audi bmw     Scrape specific brands
    scrape --objetivos           Scrape from objetivos table
    status                       Show database statistics
    brands                       List available brands
    export output.json           Export data to file

Examples:
    python main.py                           # Launch GUI
    python main.py cli scrape --marcas audi  # Scrape Audi
    python main.py cli status                # Show stats
"""

import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))


def main():
    """Main entry point."""
    # Check if CLI mode
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        # Remove 'cli' from args and run CLI
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from scraping.sites.autocasion.app.runner import main as cli_main
        cli_main()
    else:
        # Run GUI
        print("Starting Autocasion Scraper GUI...")
        from scraping.sites.autocasion.app.gui import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()
