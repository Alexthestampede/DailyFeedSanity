#!/bin/bash
# DailyFeedSanity launcher script

# Change to the script's directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run setup.sh first to create the virtual environment:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if --config flag is passed
if [ "$1" = "--config" ]; then
    # Run the configuration wizard
    python -m src.utils.config_wizard
else
    # Run the RSS processor with any passed arguments
    python -m src.main "$@"
fi