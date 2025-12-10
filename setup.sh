#!/bin/bash

# DailyFeedSanity Setup Script for Linux/Mac
# This script checks dependencies and runs the configuration wizard

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  DailyFeedSanity Setup Script  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}[1/5] Checking Python installation...${NC}"

# Check if Python 3 is installed
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"
elif command -v python &> /dev/null; then
    # Check if 'python' is Python 3
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    if [[ $PYTHON_VERSION == 3* ]]; then
        PYTHON_CMD="python"
        echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}✗ Python 3 is required but not found.${NC}"
        echo -e "${YELLOW}  Please install Python 3.8 or later from https://www.python.org/${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python is not installed.${NC}"
    echo -e "${YELLOW}  Please install Python 3.8 or later from https://www.python.org/${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[2/5] Checking pip installation...${NC}"

# Check if pip is available
if $PYTHON_CMD -m pip --version &> /dev/null; then
    PIP_VERSION=$($PYTHON_CMD -m pip --version | awk '{print $2}')
    echo -e "${GREEN}✓ pip found: $PIP_VERSION${NC}"
else
    echo -e "${RED}✗ pip is not installed.${NC}"
    echo -e "${YELLOW}  Installing pip...${NC}"

    # Try to install pip
    if command -v curl &> /dev/null; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        $PYTHON_CMD get-pip.py
        rm get-pip.py
    elif command -v wget &> /dev/null; then
        wget https://bootstrap.pypa.io/get-pip.py
        $PYTHON_CMD get-pip.py
        rm get-pip.py
    else
        echo -e "${RED}✗ Unable to install pip automatically.${NC}"
        echo -e "${YELLOW}  Please install pip manually and run this script again.${NC}"
        exit 1
    fi

    if $PYTHON_CMD -m pip --version &> /dev/null; then
        echo -e "${GREEN}✓ pip installed successfully${NC}"
    else
        echo -e "${RED}✗ pip installation failed.${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}[3/5] Installing/Updating Python dependencies...${NC}"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt not found!${NC}"
    exit 1
fi

# Install requirements
echo -e "${YELLOW}  This may take a few minutes...${NC}"
if $PYTHON_CMD -m pip install -r requirements.txt --quiet --upgrade; then
    echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Some dependencies may have failed to install.${NC}"
    echo -e "${YELLOW}  You can try running manually: $PYTHON_CMD -m pip install -r requirements.txt${NC}"
fi

echo ""
echo -e "${BLUE}[4/5] Checking RSS feed configuration...${NC}"

# Check if rss.txt exists
if [ -f "rss.txt" ]; then
    FEED_COUNT=$(grep -c "^https\?://" rss.txt 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ rss.txt found with $FEED_COUNT feed(s)${NC}"
else
    echo -e "${YELLOW}⚠ rss.txt not found${NC}"
    echo -e "${YELLOW}  You will need to add RSS feeds using the configuration wizard.${NC}"
    echo -e "${YELLOW}  The wizard will help you add your first feeds.${NC}"
fi

echo ""
echo -e "${BLUE}[5/5] Checking AI provider (optional)...${NC}"

# Check if Ollama is running (non-blocking)
if command -v curl &> /dev/null; then
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓ Ollama detected and running on localhost:11434${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama not detected (this is optional)${NC}"
        echo -e "${YELLOW}  You can use other AI providers like Gemini, OpenAI, or Claude.${NC}"
        echo -e "${YELLOW}  The configuration wizard will help you set this up.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ curl not available, skipping Ollama check${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Setup Complete!              ${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Run the configuration wizard to set up your AI provider and RSS feeds:"
echo -e "     ${YELLOW}$PYTHON_CMD -m src.utils.config_wizard${NC}"
echo ""
echo -e "  2. After configuration, run the processor:"
echo -e "     ${YELLOW}$PYTHON_CMD -m src.main${NC}"
echo ""

# Ask if user wants to run the configuration wizard now
echo -e "${BLUE}Would you like to run the configuration wizard now? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Starting configuration wizard...${NC}"
    echo ""
    $PYTHON_CMD -m src.utils.config_wizard
else
    echo -e "${YELLOW}You can run the wizard later with: $PYTHON_CMD -m src.utils.config_wizard${NC}"
fi

echo ""
echo -e "${GREEN}Thank you for using DailyFeedSanity!${NC}"
