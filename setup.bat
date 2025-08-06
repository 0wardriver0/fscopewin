@echo off
chcp 65001 >nul
echo 🚀 Setting up System Overview Monitor...

:: Check if Python 3 is installed
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed. Please install Python 3.7+
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo ⚡ Activating virtual environment...
call venv\Scripts\activate.bat

:: Install pip packages
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

:: Ensure script is executable (Not needed on Windows, but simulate intent)
echo Making sure sysmon.py is ready to run...

echo ✅ Setup complete!
echo.
echo 🎯 To run the system monitor:
echo   First activate the virtual environment:
echo     call venv\Scripts\activate.bat
echo   Then run:
echo     python sysmon.py
echo.
echo 💡 Press Ctrl+C to exit when running
echo 🔄 Run "deactivate" to exit the virtual environment
