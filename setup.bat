@echo off
chcp 65001 >nul
echo 🚀 Setting up System Overview Monitor...

:: Step 1: Ensure Python is installed
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed. Please install Python 3.7+
    exit /b 1
)

:: Step 2: Create virtual environment if it doesn't exist
if not exist venv (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

:: Step 3: Set PowerShell execution policy
echo ⚙️  Setting PowerShell execution policy (CurrentUser) to RemoteSigned...
powershell -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force"

:: Step 4: Activate venv and run setup in PowerShell
echo ⚡ Activating virtual environment and running project...
powershell -ExecutionPolicy Bypass -NoExit -Command "& { .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python sysmon.py }"
