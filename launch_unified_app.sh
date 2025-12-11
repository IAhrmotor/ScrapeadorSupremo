#!/bin/bash
# Launcher for Unified Scraper Application (Linux/Mac)
# Make executable: chmod +x launch_unified_app.sh
# Run: ./launch_unified_app.sh

echo "========================================"
echo "  Unified Scraper Application"
echo "  Autocasion + Cochesnet Manager"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run application
echo "Starting application..."
python3 scraping/unified_app/main.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application failed to start"
    read -p "Press Enter to close..."
fi
