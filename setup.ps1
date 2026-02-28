# DailyFeedSanity Setup Script for Windows (PowerShell)
# This script checks dependencies and runs the configuration wizard
#
# Usage: Right-click -> "Run with PowerShell"
#    or: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

# --- Colors ---
function Write-Step   { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Ok     { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warn   { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Err    { param($msg) Write-Host $msg -ForegroundColor Red }

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  DailyFeedSanity Setup Script  " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Change to the directory where the script lives
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# ---------------------------------------------------------------
# [1/6] Check Python installation
# ---------------------------------------------------------------
Write-Step "[1/6] Checking Python installation..."

$PythonCmd = $null

# Helper: test a python command, reject the Microsoft Store stub
function Test-Python {
    param($cmd)
    try {
        $info = & $cmd --version 2>&1
        # The MS Store stub lives under WindowsApps and returns an error or opens the Store
        $exePath = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
        if ($exePath -and $exePath -match "WindowsApps") {
            return $null  # MS Store stub, not real Python
        }
        if ($info -match "Python\s+3\.") {
            return $cmd
        }
    } catch {
        # command not found or errored
    }
    return $null
}

$PythonCmd = Test-Python "python"
if (-not $PythonCmd) { $PythonCmd = Test-Python "python3" }
if (-not $PythonCmd) { $PythonCmd = Test-Python "py" }

if ($PythonCmd) {
    $ver = & $PythonCmd --version 2>&1
    Write-Ok "  [OK] $ver"
} else {
    Write-Warn "  Python 3 not found. Attempting to install via winget..."
    try {
        winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        # Refresh PATH so the new install is visible in this session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                     [System.Environment]::GetEnvironmentVariable("Path", "User")
        $PythonCmd = Test-Python "python"
        if (-not $PythonCmd) { $PythonCmd = Test-Python "python3" }
        if (-not $PythonCmd) { $PythonCmd = Test-Python "py" }
    } catch {
        # winget not available or install failed
    }

    if ($PythonCmd) {
        $ver = & $PythonCmd --version 2>&1
        Write-Ok "  [OK] Installed $ver"
    } else {
        Write-Err "  [X] Could not install Python automatically."
        Write-Warn "  Please download Python 3.10+ from https://www.python.org/downloads/"
        Write-Warn "  IMPORTANT: Check 'Add Python to PATH' during installation."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# ---------------------------------------------------------------
# [2/6] Check pip
# ---------------------------------------------------------------
Write-Host ""
Write-Step "[2/6] Checking pip..."

$pipCheck = & $PythonCmd -m pip --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "  [OK] $pipCheck"
} else {
    Write-Warn "  pip not found. Attempting to bootstrap..."
    & $PythonCmd -m ensurepip --upgrade 2>&1 | Out-Null
    $pipCheck = & $PythonCmd -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "  [OK] pip installed: $pipCheck"
    } else {
        Write-Err "  [X] pip installation failed."
        Write-Warn "  Try: $PythonCmd -m ensurepip --upgrade"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# ---------------------------------------------------------------
# [3/6] Set up virtual environment
# ---------------------------------------------------------------
Write-Host ""
Write-Step "[3/6] Setting up virtual environment..."

if (-not (Test-Path ".venv")) {
    Write-Warn "  Creating virtual environment..."
    & $PythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Err "  [X] Failed to create virtual environment."
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Ok "  [OK] Virtual environment created"
} else {
    Write-Ok "  [OK] Virtual environment already exists"
}

# Activate the venv
Write-Warn "  Activating virtual environment..."
& ".venv\Scripts\Activate.ps1"

# Upgrade pip inside venv
Write-Warn "  Upgrading pip..."
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# ---------------------------------------------------------------
# [4/6] Install dependencies
# ---------------------------------------------------------------
Write-Host ""
Write-Step "[4/6] Installing/Updating Python dependencies..."

if (-not (Test-Path "requirements.txt")) {
    Write-Err "  [X] requirements.txt not found!"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Warn "  This may take a few minutes..."
python -m pip install -r requirements.txt --quiet --upgrade 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "  [OK] All dependencies installed successfully"
} else {
    Write-Warn "  [!] Some dependencies may have failed."
    Write-Warn "  You can try manually:"
    Write-Warn "    .venv\Scripts\Activate.ps1"
    Write-Warn "    python -m pip install -r requirements.txt"
}

# ---------------------------------------------------------------
# [5/6] Check RSS feed configuration
# ---------------------------------------------------------------
Write-Host ""
Write-Step "[5/6] Checking RSS feed configuration..."

if (Test-Path "rss.txt") {
    $feedCount = (Select-String -Path "rss.txt" -Pattern "^https?://" | Measure-Object).Count
    Write-Ok "  [OK] rss.txt found with $feedCount feed(s)"
} else {
    Write-Warn "  [!] rss.txt not found"
    Write-Warn "  You will need to add RSS feeds using the configuration wizard."
}

# ---------------------------------------------------------------
# [6/6] Check AI provider (optional)
# ---------------------------------------------------------------
Write-Host ""
Write-Step "[6/6] Checking AI provider (optional)..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Ok "  [OK] Ollama detected and running on localhost:11434"
    }
} catch {
    Write-Warn "  [!] Ollama not detected (this is optional)"
    Write-Warn "  You can use other AI providers like Gemini, OpenAI, or Claude."
    Write-Warn "  The configuration wizard will help you set this up."
}

# ---------------------------------------------------------------
# Done
# ---------------------------------------------------------------
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "  Setup Complete!              " -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Step "Next steps:"
Write-Host "  1. Run the configuration wizard to set up your AI provider and RSS feeds:"
Write-Warn "     .\dailyfeedsanity.bat --config"
Write-Warn "     OR: .venv\Scripts\Activate.ps1 ; python -m src.utils.config_wizard"
Write-Host ""
Write-Host "  2. After configuration, run the processor:"
Write-Warn "     .\dailyfeedsanity.bat"
Write-Warn "     OR: .venv\Scripts\Activate.ps1 ; python -m src.main"
Write-Host ""

# Ask user if they want to run the wizard now
$answer = Read-Host "Would you like to run the configuration wizard now? (y/n)"
if ($answer -match "^[Yy]$") {
    Write-Host ""
    Write-Step "Starting configuration wizard..."
    Write-Host ""
    python -m src.utils.config_wizard
} else {
    Write-Warn "You can run the wizard later with: .\dailyfeedsanity.bat --config"
}

Write-Host ""
Write-Ok "Thank you for using DailyFeedSanity!"
Write-Host ""
Read-Host "Press Enter to close"
