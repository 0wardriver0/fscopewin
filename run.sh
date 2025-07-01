#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment and run the monitor
echo "🚀 Starting System Overview Monitor..."
source venv/bin/activate && python3 sysmon.py 