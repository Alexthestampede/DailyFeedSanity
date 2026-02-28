@echo off
REM DailyFeedSanity launcher script for Windows
REM Usage:
REM   dailyfeedsanity.bat              - Run the RSS processor
REM   dailyfeedsanity.bat --config     - Run the configuration wizard
REM   dailyfeedsanity.bat --debug      - Run with debug logging
REM   dailyfeedsanity.bat [any args]   - Passed through to src.main

REM Change to the directory where this script lives
cd /d "%~dp0"

REM --- Check virtual environment ---
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ERROR: Virtual environment not found!
    echo Please run setup.ps1 first to create the virtual environment:
    echo.
    echo   powershell -ExecutionPolicy Bypass -File setup.ps1
    echo.
    pause
    exit /b 1
)

REM --- Activate virtual environment ---
call ".venv\Scripts\activate.bat"

REM --- Check that python works inside the venv ---
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found in the virtual environment.
    echo Try re-running setup.ps1 to recreate the venv.
    echo.
    pause
    exit /b 1
)

REM --- Handle --config flag ---
if "%~1"=="--config" (
    python -m src.utils.config_wizard
    goto :end
)

REM --- Run the RSS processor with all arguments ---
python -m src.main %*

:end
