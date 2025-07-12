#!/bin/bash

# SprintReader Stage 3 - Enhanced Application Launcher
# Runs the complete PDF reader with timer modes and focus features

set -e

echo "🎯 Starting SprintReader Stage 3 - Focused Reading & Productivity"
echo "================================================================"

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Please run this script from the sprintreader project directory"
    exit 1
fi

# Activate virtual environment
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Please run setup first"
    exit 1
fi

source venv/bin/activate

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "❌ Database not initialized. Please run ./init_stage3.sh first"
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

# Launch SprintReader Stage 3
echo "🚀 Launching SprintReader Stage 3..."
echo ""
echo "🎯 Stage 3 Features:"
echo "  🍅 Pomodoro Timer (25 min focus + 5 min breaks)"
echo "  ⚡ Sprint Sessions (5 min quick reading bursts)"
echo "  🎯 Focus Mode (distraction-free interface)"
echo "  📊 Enhanced Analytics (reading insights & trends)"
echo "  🔔 Smart Notifications (progress reminders)"
echo "  🔥 Reading Streaks (habit building)"
echo ""
echo "📖 Stage 2 Foundation:"
echo "  • PDF viewer with time tracking"
echo "  • Reading speed calculation"
echo "  • Progress saving and resume"
echo "  • Zoom controls & navigation"
echo ""
echo "⌨️ Quick Start:"
echo "  • Ctrl+O: Open PDF file"
echo "  • Choose timer mode and click Start"
echo "  • F11: Toggle Focus Mode"
echo "  • Menu > Analytics: View progress"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

cd src && python main_stage3.py

echo ""
echo "👋 SprintReader Stage 3 session ended"
