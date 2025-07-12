#!/bin/bash

# SprintReader Quick Setup Script
echo "🚀 SprintReader Quick Setup"
echo "=========================="

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Please run this script from the SprintReader project directory"
    exit 1
fi

# Check Python
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not found. Installing with Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    brew install postgresql
fi

# Start PostgreSQL if not running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "🔄 Starting PostgreSQL..."
    brew services start postgresql
    sleep 3
fi

echo "✅ PostgreSQL is running"

# Create virtual environment
if [[ ! -d "venv" ]]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "⚙️ Creating .env file..."
    cat > .env << 'EOF'
# SprintReader Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprintreader
DB_USER=sprintreader_user
DB_PASSWORD=sprintreader_local_pass
DATABASE_URL=postgresql://sprintreader_user:sprintreader_local_pass@localhost:5432/sprintreader

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
EOF
fi

# Source environment variables
source .env

# Setup PostgreSQL database
echo "🗄️ Setting up database..."

# Find PostgreSQL superuser
PG_SUPERUSER="postgres"
if ! psql -h $DB_HOST -p $DB_PORT -U postgres -c "SELECT 1;" &> /dev/null 2>&1; then
    PG_SUPERUSER=$(whoami)
fi

# Create database user
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;
" > /dev/null 2>&1

# Create database
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\\gexec
" > /dev/null 2>&1

# Grant privileges
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
" > /dev/null 2>&1

# Test database connection
echo "🔌 Testing database connection..."
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
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Initialize database
echo "📊 Initializing database tables..."
cd src && python3 -c "
from database.models import db_manager, initialize_stage5_settings

try:
    db_manager.create_tables()
    initialize_stage5_settings()
    print('✅ Database tables created')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
" && cd ..

# Create directories
mkdir -p logs
mkdir -p vaults
mkdir -p vaults/General

# Create sample note
cat > vaults/General/Welcome.md << 'EOF'
---
id: welcome-note
topic_id: general
document_id: 0
page_number: 1
created_at: 2024-01-01T12:00:00
updated_at: 2024-01-01T12:00:00
tags: [welcome, getting-started]
---

# Welcome to SprintReader!

## Getting Started

Welcome to SprintReader! This is your first note to demonstrate the note-taking system.

### Quick Start:
1. Open a PDF with Ctrl+O
2. Start a timer with Ctrl+P (Pomodoro) or Ctrl+S (Sprint)
3. Select text in the PDF to create notes
4. Use F11 for Focus Mode

### Features:
- 📖 Smart PDF reading with time estimation
- ⏱️ Pomodoro and Sprint timers
- 🎯 Focus modes for concentration
- 📝 Highlight-to-note functionality
- 📊 Reading analytics and insights

Happy reading! 📚
EOF

# Create run script
cat > run.sh << 'EOF'
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
EOF

chmod +x run.sh

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "✅ Virtual environment created"
echo "✅ Dependencies installed"
echo "✅ Database configured"
echo "✅ Application ready"
echo ""
echo "🚀 To start SprintReader:"
echo "   ./run.sh"
echo ""
echo "🎯 Quick Start:"
echo "   1. Open a PDF (Ctrl+O)"
echo "   2. Start timer (Ctrl+P for Pomodoro, Ctrl+S for Sprint)"
echo "   3. Enable Focus Mode (F11)"
echo "   4. Select text to create notes"
echo ""
echo "📚 Happy focused reading!"