@echo off
REM DailyFeedSanity Setup Script for Windows
REM This script checks dependencies and runs the configuration wizard

setlocal enabledelayedexpansion

echo ================================
echo   DailyFeedSanity Setup Script
echo ================================
echo.

REM Get the directory where the script is located
cd /d "%~dp0"

echo [1/5] Checking Python installation...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Python found: !PYTHON_VERSION!
    set PYTHON_CMD=python
) else (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo [OK] Python 3 found: !PYTHON_VERSION!
        set PYTHON_CMD=python3
    ) else (
        echo [ERROR] Python is not installed.
        echo   Please install Python 3.8 or later from https://www.python.org/
        echo   Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

echo.
echo [2/5] Checking pip installation...

REM Check if pip is available
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('%PYTHON_CMD% -m pip --version 2^>^&1') do set PIP_VERSION=%%i
    echo [OK] pip found: !PIP_VERSION!
) else (
    echo [ERROR] pip is not installed.
    echo   Installing pip...

    REM Try to install pip
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py >nul 2>&1
    if %errorlevel% equ 0 (
        %PYTHON_CMD% get-pip.py
        del get-pip.py
    ) else (
        echo [ERROR] Unable to install pip automatically.
        echo   Please install pip manually and run this script again.
        pause
        exit /b 1
    )

    %PYTHON_CMD% -m pip --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] pip installed successfully
    ) else (
        echo [ERROR] pip installation failed.
        pause
        exit /b 1
    )
)

echo.
echo [3/5] Installing/Updating Python dependencies...

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

REM Install requirements
echo   This may take a few minutes...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet --upgrade
if %errorlevel% equ 0 (
    echo [OK] All dependencies installed successfully
) else (
    echo [WARNING] Some dependencies may have failed to install.
    echo   You can try running manually: %PYTHON_CMD% -m pip install -r requirements.txt
)

echo.
echo [4/5] Checking RSS feed configuration...

REM Check if rss.txt exists
if exist "rss.txt" (
    REM Count feeds (lines starting with http)
    set FEED_COUNT=0
    for /f "tokens=*" %%i in ('findstr /r "^https*://" rss.txt 2^>nul') do set /a FEED_COUNT+=1
    echo [OK] rss.txt found with !FEED_COUNT! feed(s)
) else (
    echo [WARNING] rss.txt not found
    echo   You will need to add RSS feeds using the configuration wizard.
    echo   The wizard will help you add your first feeds.
)

echo.
echo [5/5] Checking AI provider (optional)...

REM Check if Ollama is running (non-blocking)
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama detected and running on localhost:11434
) else (
    echo [WARNING] Ollama not detected (this is optional)
        echo   You can use other AI providers like Gemini, OpenAI, or Claude.
        echo   The configuration wizard will help you set this up.
    )
)

echo.
echo ================================
echo   Setup Complete!
echo ================================
echo.
echo Next steps:
echo   1. Run the configuration wizard to set up your AI provider and RSS feeds:
echo      %PYTHON_CMD% -m src.utils.config_wizard
echo.
echo   2. After configuration, run the processor:
echo      %PYTHON_CMD% -m src.main
echo.

REM Ask if user wants to run the configuration wizard now
set /p response="Would you like to run the configuration wizard now? (y/n): "

if /i "!response!" equ "y" (
    echo.
    echo Starting configuration wizard...
    echo.
    %PYTHON_CMD% -m src.utils.config_wizard
) else (
    echo You can run the wizard later with: %PYTHON_CMD% -m src.utils.config_wizard
)

echo.
echo Thank you for using DailyFeedSanity!
echo.
pause
