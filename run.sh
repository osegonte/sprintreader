#!/bin/bash

# SprintReader - Main Application Launcher
# Runs the complete PDF viewer with time tracking

set -e

echo "📖 Starting SprintReader - PDF Reading & Time Tracking"
echo "====================================================="

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Please run this script from the sprintreader project directory"
    exit 1
fi

# Activate virtual environment
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

source venv/bin/activate

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "❌ Database not initialized. Please run ./init_database.sh first"
    exit 1
fi

source .env

# Quick database connection check
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Create logs directory
mkdir -p logs

# Launch SprintReader
echo "🚀 Launching SprintReader..."
echo ""
echo "📖 Features available:"
echo "  • PDF viewer with time tracking"
echo "  • Automatic reading speed calculation"
echo "  • Progress saving and resume reading"
echo "  • Keyboard shortcuts (←/→, Ctrl++/-)"
echo ""
echo "🎮 Controls:"
echo "  • Ctrl+O: Open PDF file"
echo "  • ←/→: Navigate pages"
echo "  • Ctrl++/Ctrl+-: Zoom in/out"
echo "  • Ctrl+Q: Quit application"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

cd src && python main.py

echo ""
echo "👋 SprintReader session ended"
