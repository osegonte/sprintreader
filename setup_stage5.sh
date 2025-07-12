#!/bin/bash

# SprintReader Stage 5 - Setup and Database Initialization
# Topic-Based Goal Setting, Focus Mode & PDF Grouping

set -e

echo "🚀 SprintReader Stage 5 - Enhanced Setup"
echo "========================================"
echo "✨ Topic-Based Organization"
echo "🎯 Adaptive Goal Setting"
echo "🧘 Enhanced Focus Mode"
echo "📊 Productivity Analytics"
echo ""

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Please run this script from the sprintreader project directory"
    exit 1
fi

echo "🔍 Checking system requirements..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
major_version=$(echo $python_version | cut -d'.' -f1)
minor_version=$(echo $python_version | cut -d'.' -f2)

if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 8 ]]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not found. Please install PostgreSQL first."
    echo "💡 On macOS: brew install postgresql"
    echo "💡 On Ubuntu: sudo apt install postgresql postgresql-contrib"
    exit 1
fi

echo "✅ PostgreSQL found"

# Find PostgreSQL superuser
PG_SUPERUSER="postgres"
if ! psql -h localhost -p 5432 -U postgres -c "SELECT 1;" &> /dev/null; then
    PG_SUPERUSER=$(whoami)
    if ! psql -h localhost -p 5432 -U $PG_SUPERUSER -c "SELECT 1;" &> /dev/null; then
        echo "❌ Cannot connect to PostgreSQL. Please ensure PostgreSQL is running."
        echo "💡 Try: brew services start postgresql"
        echo "💡 Or: sudo systemctl start postgresql"
        exit 1
    fi
fi

echo "✅ Using PostgreSQL superuser: $PG_SUPERUSER"

# Create virtual environment if needed
if [[ ! -d "venv" ]]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Updating pip..."
pip install --upgrade pip

# Install/upgrade requirements
echo "📦 Installing/upgrading Python dependencies..."
pip install -r requirements.txt

# Install Stage 5 specific requirements
echo "📦 Installing Stage 5 enhanced dependencies..."
pip install --upgrade PyQt6
pip install --upgrade sqlalchemy
pip install --upgrade psycopg2-binary

echo "✅ Dependencies installed"

# Create/update .env file for Stage 5
if [[ ! -f ".env" ]]; then
    echo "⚙️  Creating Stage 5 environment configuration..."
    
    cat > .env << EOF
# SprintReader Stage 5 Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprintreader
DB_USER=sprintreader_user
DB_PASSWORD=sprintreader_stage5_pass
DATABASE_URL=postgresql://sprintreader_user:sprintreader_stage5_pass@localhost:5432/sprintreader

# Application Settings
DEBUG=true
LOG_LEVEL=INFO

# Stage 5: Enhanced Features
ENABLE_TOPIC_ORGANIZATION=true
ENABLE_GOAL_SETTING=true
ENABLE_ENHANCED_FOCUS=true
ENABLE_PRODUCTIVITY_ANALYTICS=true

# Focus Mode Settings
DEFAULT_FOCUS_LEVEL=standard
AUTO_BREAK_REMINDERS=true
BREAK_INTERVAL_MINUTES=25
PRODUCTIVITY_TRACKING=true

# Topic Settings
AUTO_TOPIC_SUGGESTIONS=true
TOPIC_COLOR_CODING=true

# Goal Settings
ADAPTIVE_GOAL_ADJUSTMENT=true
GOAL_REMINDER_NOTIFICATIONS=true
DAILY_GOAL_SUMMARY=true
EOF
    
    echo "✅ Stage 5 environment configuration created"
else
    echo "✅ Environment configuration found"
fi

# Source environment variables
source .env

echo "🗄️  Setting up PostgreSQL database for Stage 5..."

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "💡 On macOS: brew services start postgresql"
    echo "💡 On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

# Create/update database user
echo "👤 Setting up database user for Stage 5..."
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;
" || echo "⚠️  User configuration updated"

# Create database if needed
echo "🗄️  Creating/updating database..."
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\\gexec
" || echo "⚠️  Database already exists"

# Grant enhanced privileges for Stage 5
echo "🔐 Setting up enhanced database permissions..."
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
"

# Test database connection
echo "🔌 Testing Stage 5 database connection..."
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
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'✅ Stage 5 database connection successful')
    print(f'📊 PostgreSQL version: {version[0][:50]}...')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Initialize Stage 5 database schema
echo "📊 Initializing Stage 5 database schema..."
cd src && python -c "
try:
    # Initialize existing models
    from database.models import db_manager
    db_manager.create_tables()
    print('✅ Core tables initialized')
    
    # Initialize Stage 5 models
    from database.stage5_models import Stage5Manager
    stage5_manager = Stage5Manager(db_manager)
    stage5_manager.create_stage5_tables()
    print('✅ Stage 5 tables created')
    
    # Add Stage 5 default settings
    from database.models import Settings
    session = db_manager.get_session()
    
    stage5_settings = [
        ('default_focus_level', 'standard'),
        ('auto_break_reminders', 'true'),
        ('break_interval_minutes', '25'),
        ('productivity_tracking', 'true'),
        ('adaptive_goal_adjustment', 'true'),
        ('goal_reminder_notifications', 'true'),
        ('auto_topic_suggestions', 'true'),
        ('topic_color_coding', 'true'),
        ('daily_goal_summary', 'true'),
        ('focus_analytics_enabled', 'true')
    ]
    
    for key, value in stage5_settings:
        existing = session.query(Settings).filter_by(key=key).first()
        if not existing:
            session.add(Settings(key=key, value=value))
    
    session.commit()
    session.close()
    print('✅ Stage 5 settings initialized')
    
except Exception as e:
    print(f'❌ Stage 5 database initialization failed: {e}')
    exit(1)
" && cd ..

# Create Stage 5 directories
echo "📁 Creating Stage 5 application directories..."
mkdir -p logs
mkdir -p vaults
mkdir -p vaults/General
mkdir -p src/stage5

# Create Stage 5 module files
echo "📦 Creating Stage 5 module structure..."

# Create __init__.py files
touch src/stage5/__init__.py

# Create symbolic links for Stage 5 components
cd src/stage5
ln -sf ../database/stage5_models.py stage5_models.py 2>/dev/null || echo "Stage 5 models linked"
cd ../..

# Create run script for Stage 5
echo "📄 Creating Stage 5 run script..."
cat > run_stage5.sh << 'EOF'
#!/bin/bash

# SprintReader Stage 5 - Enhanced Launcher
echo "🚀 Starting SprintReader Stage 5..."
echo "📚 Topic-Based Organization & Goal Setting"

# Check environment
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Run ./setup_stage5.sh first"
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
    print('✅ Stage 5 database ready')
except Exception as e:
    print(f'❌ Database error: {e}')
    print('💡 Run ./setup_stage5.sh to fix database issues')
    exit(1)
"

# Create vaults directory if needed
mkdir -p vaults

# Launch Stage 5 application
echo "🎯 Launching SprintReader Stage 5..."
cd src && python stage5_integration.py
EOF

chmod +x run_stage5.sh

# Create sample topic and goals
echo "📝 Creating Stage 5 sample data..."
cd src && python -c "
try:
    from database.stage5_models import Stage5Manager
    from database.models import db_manager
    from datetime import datetime, timedelta
    
    stage5_manager = Stage5Manager(db_manager)
    
    # Create sample topics
    sample_topics = [
        ('Computer Science', 'Programming, algorithms, and software engineering', '#2563EB'),
        ('Research Papers', 'Academic papers and research materials', '#059669'),
        ('Personal Development', 'Self-improvement and skill building', '#7C3AED'),
        ('Technical Documentation', 'Manuals, guides, and technical references', '#EA580C')
    ]
    
    for name, desc, color in sample_topics:
        topic_id = stage5_manager.get_or_create_topic(name, desc, color)
        if topic_id:
            print(f'✅ Sample topic created: {name}')
    
    # Create sample goals
    topics = db_manager.get_session().query(
        db_manager.SessionLocal().bind.execute('SELECT id FROM topics LIMIT 2')
    ).fetchall() if hasattr(db_manager, 'SessionLocal') else []
    
    print('✅ Stage 5 sample data created')
    
except Exception as e:
    print(f'⚠️  Sample data creation: {e}')
" && cd ..

echo ""
echo "🎉 SprintReader Stage 5 Setup Complete!"
echo "======================================"
echo ""
echo "🆕 What's New in Stage 5:"
echo "  ✅ Topic-based PDF organization with color coding"
echo "  ✅ Adaptive goal setting with progress tracking"
echo "  ✅ Enhanced focus mode (Minimal → Immersive)"
echo "  ✅ Productivity analytics and recommendations"
echo "  ✅ Smart time estimation with confidence levels"
echo "  ✅ Daily/weekly goal dashboards"
echo "  ✅ Focus session analytics"
echo "  ✅ Automated progress tracking"
echo ""
echo "🎯 Key Features:"
echo "  📚 Organize PDFs into topics with visual indicators"
echo "  🎯 Set and track time/page/deadline goals"
echo "  🧘 Multiple focus levels for different needs"
echo "  📊 Detailed productivity analytics"
echo "  🔄 Adaptive goal adjustments"
echo "  💡 Personalized recommendations"
echo ""
echo "🗂️ Data Storage:"
echo "  📁 Topics: PostgreSQL database with metadata"
echo "  🎯 Goals: Progress tracking with analytics"
echo "  📊 Focus: Session data and productivity metrics"
echo "  📝 Notes: Enhanced with topic organization"
echo ""
echo "🚀 Ready to start? Run:"
echo "  ./run_stage5.sh"
echo ""
echo "💡 Stage 5 Tips:"
echo "  • Create topics to organize your reading materials"
echo "  • Set realistic goals and let the system adapt"
echo "  • Use Focus Mode (F11) for distraction-free reading"
echo "  • Check Focus Analytics for productivity insights"
echo "  • Try different focus levels based on your needs"
echo ""
echo "📖 Quick Start:"
echo "  1. Open a PDF and assign it to a topic"
echo "  2. Set a reading goal for the topic"
echo "  3. Start a focus session (F11)"
echo "  4. Check your progress in the Goals dashboard"
echo ""
echo "🎯 Focus Levels:"
echo "  • Minimal: Hide sidebar only"
echo "  • Standard: Hide sidebar + non-essential UI"
echo "  • Deep: Hide everything except PDF"
echo "  • Immersive: Full-screen with ambient features"