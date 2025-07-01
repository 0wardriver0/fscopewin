#!/bin/bash

echo "🚀 Setting up System Overview Monitor..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.7+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install pip packages
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Make the script executable
chmod +x sysmon.py

echo "✅ Setup complete!"
echo ""
echo "🎯 To run the system monitor:"
echo "   First activate the virtual environment:"
echo "   source venv/bin/activate"
echo "   Then run:"
echo "   ./sysmon.py"
echo "   or"
echo "   python3 sysmon.py"
echo ""
echo "💡 Press Ctrl+C to exit when running"
echo "🔄 Run 'deactivate' to exit the virtual environment" 