#!/bin/bash

# Azure Linux Base Image Tool - Web UI Startup Script

echo "🚀 Starting Azure Linux Base Image Tool Web UI..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the web_ui directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Check if database exists
DB_PATH="../azure_linux_images.db"
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  Warning: Database not found at $DB_PATH"
    echo "   Run a scan first using the CLI tool or use the web UI scan feature"
fi

# Start the web server
echo "🌐 Starting web server on http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""

export FLASK_APP=app.py
export FLASK_ENV=development
python app.py
