#!/bin/bash

echo "🚀 Starting SprintReader..."

# Check virtual environment
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check database
python3 -c "
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
    print(f'❌ Database error: {e}')
    print('💡 Try: brew services start postgresql')
    exit(1)
"

# Launch SprintReader
echo "📖 Launching SprintReader..."
cd src && python3 main.py
