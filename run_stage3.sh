#!/bin/bash

# SprintReader Stage 3 - Enhanced Application Launcher
set -e

echo "🎯 Starting SprintReader Stage 3 - Enhanced PDF Reader"
echo "====================================================="

# Check environment
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source venv/bin/activate

# Load environment variables
if [[ ! -f ".env" ]]; then
    echo "❌ .env file not found"
    exit 1
fi

source .env

# Quick database check using same settings as Stage 2
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'sprintreader'),
        user=os.getenv('DB_USER', 'sprintreader_user'),
        password=os.getenv('DB_PASSWORD', 'sprintreader_local_pass')
    )
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database error: {e}')
    print('💡 Try running ./run.sh first to ensure database is working')
    exit(1)
"

echo ""
echo "🚀 Launching SprintReader Stage 3..."
echo ""
echo "🎯 Enhanced Features Available:"
echo "  🍅 Pomodoro Timer (25 min focus + 5 min breaks)"
echo "  ⚡ Sprint Sessions (5 min quick reading bursts)"
echo "  🎯 Focus Mode (F11 - distraction-free interface)"
echo "  📊 Enhanced Analytics (Menu > Analytics)"
echo "  🔔 Smart Notifications (session alerts)"
echo "  🔥 Reading Streaks (habit building)"
echo ""
echo "📖 Core Features (from Stage 2):"
echo "  • PDF viewer with smooth navigation"
echo "  • Automatic time tracking per page"
echo "  • Reading speed calculation"
echo "  • Progress saving and resume"
echo "  • Zoom controls (Ctrl +/-)"
echo ""
echo "⌨️ Quick Start Guide:"
echo "  1. Ctrl+O: Open a PDF file"
echo "  2. Select timer mode (Pomodoro/Sprint/Custom)"
echo "  3. Click 'Start Session' to begin"
echo "  4. F11: Toggle Focus Mode for distraction-free reading"
echo "  5. Menu > Analytics: View your reading insights"
echo ""
echo "🎮 Keyboard Shortcuts:"
echo "  • Ctrl+P: Quick start Pomodoro session"
echo "  • Ctrl+S: Quick start Sprint session"
echo "  • F11: Toggle Focus Mode"
echo "  • ←/→: Navigate pages"
echo "  • Ctrl++/-: Zoom in/out"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

cd src && python main_stage3.py

echo ""
echo "👋 SprintReader Stage 3 session ended"
echo "   📊 Check Menu > Analytics for your reading stats!"
