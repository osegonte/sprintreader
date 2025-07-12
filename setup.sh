#!/bin/bash

# SprintReader Stage 4 - Setup and Database Initialization
set -e

echo "📝 SprintReader Stage 4 - Setup & Database Initialization"
echo "=========================================================="

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

# Check PostgreSQL and get the correct superuser
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not found. Please install PostgreSQL first."
    echo "💡 On macOS: brew install postgresql"
    echo "💡 On Ubuntu: sudo apt install postgresql postgresql-contrib"
    exit 1
fi

echo "✅ PostgreSQL found"

# Find PostgreSQL superuser (try common options)
PG_SUPERUSER="postgres"
if ! psql -h $DB_HOST -p $DB_PORT -U postgres -c "SELECT 1;" &> /dev/null; then
    # Try current user
    PG_SUPERUSER=$(whoami)
    if ! psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "SELECT 1;" &> /dev/null; then
        echo "❌ Cannot connect to PostgreSQL. Please ensure PostgreSQL is running and you have superuser access."
        echo "💡 Try: brew services start postgresql"
        echo "💡 Or: createuser -s postgres"
        exit 1
    fi
fi

echo "✅ Using PostgreSQL superuser: $PG_SUPERUSER"

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade pip
echo "📦 Updating pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Additional Stage 4 requirements for note-taking
echo "📦 Installing Stage 4 note-taking dependencies..."
pip install markdown
pip install python-frontmatter
pip install pypandoc || echo "⚠️  pypandoc optional (for advanced exports)"

echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "⚙️  Creating environment configuration..."
    
    cat > .env << EOF
# SprintReader Stage 4 Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprintreader
DB_USER=sprintreader_user
DB_PASSWORD=sprintreader_local_pass
DATABASE_URL=postgresql://sprintreader_user:sprintreader_local_pass@localhost:5432/sprintreader

# Application Settings
DEBUG=true
LOG_LEVEL=INFO

# Stage 4: Note-taking Settings
NOTES_STORAGE_PATH=vaults
NOTES_AUTO_SAVE=true
NOTES_EXPORT_FORMAT=markdown
NOTES_SEARCH_ENABLED=true
EOF
    
    echo "✅ Environment configuration created"
else
    echo "✅ Environment configuration found"
fi

# Source environment variables
source .env

echo "🗄️  Setting up PostgreSQL database..."

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "💡 On macOS: brew services start postgresql"
    echo "💡 On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

# Create database user if it doesn't exist
echo "👤 Setting up database user..."
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;
" || echo "⚠️  User might already exist"

# Create database if it doesn't exist
echo "🗄️  Creating database..."
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\\gexec
" || echo "⚠️  Database might already exist"

# Grant privileges
echo "🔐 Setting up database permissions..."
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
"

# Test database connection
echo "🔌 Testing database connection..."
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
    print(f'✅ Database connection successful')
    print(f'📊 PostgreSQL version: {version[0][:50]}...')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Initialize database tables
echo "📊 Initializing database tables..."
cd src && python -c "
from database.models import db_manager
from database.stage3_models import extend_existing_models

try:
    # Create all tables
    db_manager.create_tables()
    print('✅ Core tables created')
    
    # Add Stage 3 settings
    from database.models import Settings
    session = db_manager.get_session()
    
    stage3_settings = extend_existing_models()
    for key, value in stage3_settings:
        existing = session.query(Settings).filter_by(key=key).first()
        if not existing:
            session.add(Settings(key=key, value=value))
    
    session.commit()
    session.close()
    print('✅ Stage 3 settings initialized')
    
    # Stage 4: Create notes storage directory
    import os
    notes_dir = '../vaults'
    if not os.path.exists(notes_dir):
        os.makedirs(notes_dir)
        print('✅ Notes storage directory created')
    else:
        print('✅ Notes storage directory exists')
    
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
" && cd ..

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p logs
mkdir -p vaults
mkdir -p vaults/General  # Default topic

# Create a sample note to demonstrate the system
echo "📝 Creating sample note..."
cat > vaults/General/Welcome_to_SprintReader.md << 'EOF'
---
id: sample-welcome-note
topic_id: general
document_id: 0
page_number: 1
created_at: 2024-01-01T12:00:00
updated_at: 2024-01-01T12:00:00
tags: [welcome, tutorial, getting-started]
---

# Welcome to SprintReader Stage 4!

## Excerpt

> This is a sample note to demonstrate the note-taking system.

## Notes

Welcome to SprintReader Stage 4! This version includes powerful note-taking features:

### Key Features

- **Highlight-to-Note**: Select text in PDFs to instantly create notes
- **Topic Organization**: Notes are automatically organized into topic vaults
- **Bidirectional Linking**: Connect notes using [[Note Name]] syntax
- **Tagging System**: Use #tags to categorize your notes
- **Fuzzy Search**: Find notes quickly across all topics
- **Local Storage**: All notes stored as markdown files for portability

### Getting Started

1. Open a PDF with Ctrl+O
2. Select text and click "Add to Notes"
3. Choose a topic or create a new one
4. Add your thoughts and insights
5. Use Ctrl+F to search your notes later

### Pro Tips

- Use [[Note Name]] to link related notes together
- Add #tags like #important #review #concept for easy filtering
- Export notes with Ctrl+E for use in other applications
- Check Menu > Analytics > Note Statistics for insights

Happy reading and note-taking!
EOF

# Create topic metadata
cat > vaults/General/.topic.json << 'EOF'
{
  "id": "general",
  "name": "General",
  "description": "Default topic for general notes and getting started",
  "created_at": "2024-01-01T12:00:00",
  "color": "#7E22CE"
}
EOF

echo "✅ Sample note created in vaults/General/"

# Create run script if it doesn't exist
if [[ ! -f "run_stage4.sh" ]]; then
    echo "📄 Creating run script..."
    # The run script content will be created separately
    touch run_stage4.sh
    chmod +x run_stage4.sh
fi

echo ""
echo "🎉 SprintReader Stage 4 Setup Complete!"
echo "======================================"
echo ""
echo "📝 What's New in Stage 4:"
echo "  ✅ Highlight-to-Note functionality"
echo "  ✅ Topic-based note organization"
echo "  ✅ Bidirectional linking support"
echo "  ✅ Tagging and metadata system"
echo "  ✅ Fuzzy search across all notes"
echo "  ✅ Local markdown export"
echo "  ✅ Note-taking analytics"
echo ""
echo "🗂️ Notes Storage:"
echo "  📁 Location: ./vaults/"
echo "  📝 Format: Markdown with YAML frontmatter"
echo "  🗂️ Organization: Topic-based folders"
echo "  🔍 Search: Full-text search across all notes"
echo ""
echo "🚀 Ready to start? Run:"
echo "  ./run_stage4.sh"
echo ""
echo "💡 Tips:"
echo "  • Your notes are stored locally in ./vaults/"
echo "  • Each topic gets its own folder"
echo "  • Notes are portable markdown files"
echo "  • Use Ctrl+F to search across all notes"
echo "  • Export with Ctrl+E for backup/sharing"
echo ""
echo "📖 Documentation:"
echo "  • Check the sample note in vaults/General/"
echo "  • Menu > Help > Keyboard Shortcuts for all hotkeys"
echo "  • Menu > Analytics > Note Statistics for insights"