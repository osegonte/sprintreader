#!/bin/bash

# SprintReader - Simple Launcher
echo "🚀 Starting SprintReader..."

# Check environment
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate

# Check database connection
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
    print('✅ Database ready')
except Exception as e:
    print(f'❌ Database error: {e}')
    print('💡 Run ./setup.sh to set up database')
    exit(1)
"

# Create vaults directory if it doesn't exist
mkdir -p vaults

# Launch application using the correct filename
echo "📝 Launching SprintReader..."
cd src && python main.py
