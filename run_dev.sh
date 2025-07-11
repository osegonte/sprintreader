#!/bin/bash

# SprintReader - Development Runner
# Starts the application in development mode

set -e

echo "🏃 Starting SprintReader Development Environment"
echo "=============================================="

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

echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    echo "❌ Database not initialized. Please run ./init_database.sh first"
    exit 1
fi

# Load environment variables
source .env

# Check database connection
echo "🔍 Checking database connection..."
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
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the application
echo "🚀 Starting SprintReader..."
echo "Press Ctrl+C to stop the application"
echo ""

# For Stage 1, we'll just run a basic test
python src/main.py

echo ""
echo "👋 SprintReader development session ended"