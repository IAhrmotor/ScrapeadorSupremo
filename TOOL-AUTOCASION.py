#!/usr/bin/env python
"""
TOOL-AUTOCASION
===============
Desktop application for scraping Autocasion.com car listings.

Usage:
    python TOOL-AUTOCASION.py              # Launch GUI
    python TOOL-AUTOCASION.py cli status   # Show status
    python TOOL-AUTOCASION.py cli scrape --marcas audi bmw --pages 3
    python TOOL-AUTOCASION.py cli scrape --objetivos --stealth
    python TOOL-AUTOCASION.py cli brands
    python TOOL-AUTOCASION.py cli export output.json

Features:
    - HeadlessX anti-detection integration
    - Supabase database storage
    - Orchestrator agent system
    - GUI and CLI interfaces

Escalation Chain:
    autocasion-scraper [JUNIOR]
        -> scraper-specialist [SENIOR]
            -> data-architect [ARCHITECT]
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scraping.sites.autocasion.app.main import main

if __name__ == "__main__":
    main()
