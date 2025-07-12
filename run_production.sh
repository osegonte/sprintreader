#!/bin/bash

# SprintReader Production Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sprintreader_production
DB_USER=sprintreader_user
DB_PASSWORD=sprintreader_secure_pass
DATABASE_URL=postgresql://sprintreader_user:sprintreader_secure_pass@localhost:5432/sprintreader_production

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Feature Flags
ADVANCED_ANALYTICS=true
TIME_ESTIMATION=true
FOCUS_MODE=true
NOTE_TAKING=true
GOAL_TRACKING=true

# Storage Paths
NOTES_STORAGE_PATH=vaults
BACKUP_PATH=backups
LOG_PATH=logs

# Performance Settings
AUTO_SAVE_INTERVAL=30
ANALYTICS_UPDATE_INTERVAL=60
ESTIMATION_UPDATE_INTERVAL=10
EOF
    
    echo -e "${GREEN}✅ Environment configuration created${NC}"
else
    echo -e "${GREEN}✅ Environment configuration found${NC}"
fi

# Source environment variables
source .env

# Find PostgreSQL superuser
echo -e "${BLUE}👤 Setting up database user...${NC}"
PG_SUPERUSER="postgres"
if ! psql -h $DB_HOST -p $DB_PORT -U postgres -c "SELECT 1;" &> /dev/null; then
    PG_SUPERUSER=$(whoami)
    if ! psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "SELECT 1;" &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to PostgreSQL as superuser${NC}"
        echo -e "${YELLOW}💡 Try: createuser -s postgres${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Using PostgreSQL superuser: $PG_SUPERUSER${NC}"

# Create database user if it doesn't exist
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
        RAISE NOTICE 'User $DB_USER created';
    ELSE
        RAISE NOTICE 'User $DB_USER already exists';
    END IF;
END
\$\$;
" > /dev/null

# Create database if it doesn't exist
echo -e "${BLUE}🗄️ Creating production database...${NC}"
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\\gexec
" > /dev/null

# Grant privileges
psql -h $DB_HOST -p $DB_PORT -U $PG_SUPERUSER -c "
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
" > /dev/null

echo -e "${GREEN}✅ Database setup complete${NC}"

# Test database connection
echo -e "${BLUE}🔌 Testing database connection...${NC}"
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
echo -e "${BLUE}📊 Initializing database schema...${NC}"
cd src && python3 -c "
from database.models import db_manager, initialize_stage5_settings
import sys

try:
    # Create all tables
    db_manager.create_tables()
    print('✅ Database tables created')
    
    # Initialize settings
    initialize_stage5_settings()
    print('✅ Application settings initialized')
    
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    sys.exit(1)
" && cd ..

# Create necessary directories
echo -e "${BLUE}📁 Creating application directories...${NC}"
mkdir -p logs
mkdir -p vaults
mkdir -p vaults/General
mkdir -p backups
mkdir -p temp

# Create application structure
mkdir -p ~/.sprintreader
mkdir -p ~/.sprintreader/themes
mkdir -p ~/.sprintreader/plugins
mkdir -p ~/.sprintreader/exports

# Set appropriate permissions
chmod 755 logs
chmod 755 vaults
chmod 755 backups
chmod 700 ~/.sprintreader

echo -e "${GREEN}✅ Directory structure created${NC}"

# Create desktop entry for easy launching (Linux/Unix)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${BLUE}🖥️ Creating desktop entry...${NC}"
    
    CURRENT_DIR=$(pwd)
    DESKTOP_ENTRY="$HOME/.local/share/applications/sprintreader.desktop"
    
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_ENTRY" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SprintReader
Comment=Focused PDF Reading & Productivity Tool
Exec=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/sprintreader_final.py
Icon=$CURRENT_DIR/assets/icon.png
Terminal=false
Categories=Education;Office;
Keywords=PDF;Reading;Productivity;Timer;Notes;
EOF
    
    chmod +x "$DESKTOP_ENTRY"
    echo -e "${GREEN}✅ Desktop entry created${NC}"
fi

# Create macOS app bundle (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}🍎 Setting up macOS integration...${NC}"
    
    # Create alias for easy terminal access
    SHELL_RC="$HOME/.zshrc"
    if [[ -f "$HOME/.bash_profile" ]]; then
        SHELL_RC="$HOME/.bash_profile"
    fi
    
    CURRENT_DIR=$(pwd)
    
    # Add alias if it doesn't exist
    if ! grep -q "alias sprintreader" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# SprintReader alias" >> "$SHELL_RC"
        echo "alias sprintreader='cd \"$CURRENT_DIR\" && ./run_production.sh'" >> "$SHELL_RC"
        echo -e "${GREEN}✅ Added 'sprintreader' command to shell${NC}"
        echo -e "${YELLOW}💡 Restart terminal or run 'source $SHELL_RC' to use the command${NC}"
    fi
fi

# Create production launcher script
echo -e "${BLUE}📜 Creating production launcher...${NC}"

cat > sprintreader_launcher.py << 'EOF'
#!/usr/bin/env python3
"""
SprintReader Production Launcher
Handles environment setup and graceful startup
"""

import sys
import os
import logging
from pathlib import Path

def setup_environment():
    """Setup environment for production"""
    # Add src to path
    src_path = Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_path))
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/sprintreader.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main launcher function"""
    try:
        # Setup environment
        setup_environment()
        
        # Import and run the main application
        from sprintreader_final import main as app_main
        app_main()
        
    except KeyboardInterrupt:
        print("\n👋 SprintReader stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start SprintReader: {e}")
        logging.critical(f"Startup failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x sprintreader_launcher.py

# Create the main production run script
cat > run_production.sh << 'EOF'
#!/bin/bash

# SprintReader Production Runner
echo "🚀 Starting SprintReader Production..."

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Please run the deployment script first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check database connection
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
    print('✅ Database connection verified')
except Exception as e:
    print(f'❌ Database error: {e}')
    print('💡 Ensure PostgreSQL is running: brew services start postgresql')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Create required directories
mkdir -p logs vaults backups

# Launch SprintReader
echo "📖 Launching SprintReader..."
python3 sprintreader_launcher.py

echo "👋 SprintReader session ended"
EOF

chmod +x run_production.sh

echo -e "${GREEN}✅ Production scripts created${NC}"

# Create backup script
echo -e "${BLUE}💾 Creating backup script...${NC}"

cat > backup_data.sh << 'EOF'
#!/bin/bash

# SprintReader Data Backup Script
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="sprintreader_backup_$TIMESTAMP"

echo "💾 Creating SprintReader backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup archive
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git" \
    --exclude="logs/*.log" \
    vaults/ \
    .env \
    src/ \
    *.py \
    *.sh \
    requirements.txt \
    README.md

# Backup database
if command -v pg_dump &> /dev/null; then
    source .env
    pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/${BACKUP_NAME}_database.sql"
    echo "✅ Database backed up"
fi

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo "📊 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)"

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t sprintreader_backup_*.tar.gz | tail -n +11 | xargs -r rm
cd ..

echo "🧹 Old backups cleaned up (keeping last 10)"
EOF

chmod +x backup_data.sh

# Create system service (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${BLUE}🔧 Creating systemd service (optional)...${NC}"
    
    CURRENT_DIR=$(pwd)
    SERVICE_FILE="$HOME/.config/systemd/user/sprintreader.service"
    
    mkdir -p "$HOME/.config/systemd/user"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=SprintReader - Focused PDF Reading Tool
After=postgresql.service

[Service]
Type=simple
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/sprintreader_launcher.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF
    
    echo -e "${GREEN}✅ Systemd service created${NC}"
    echo -e "${YELLOW}💡 Enable with: systemctl --user enable sprintreader.service${NC}"
fi

# Run initial tests
echo -e "${BLUE}🧪 Running initial tests...${NC}"

# Test Python imports
python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    from database.models import db_manager
    print('✅ Database models import successful')
    
    from ui.pdf_viewer import PDFViewerWidget
    print('✅ PDF viewer import successful')
    
    from timer.timer_manager import TimerManager
    print('✅ Timer manager import successful')
    
    from analytics.analytics_manager import AnalyticsManager
    print('✅ Analytics manager import successful')
    
    from estimation.time_estimator import TimeEstimator
    print('✅ Time estimator import successful')
    
    from focus.focus_manager import FocusManager
    print('✅ Focus manager import successful')
    
    from notifications.notification_manager import NotificationManager
    print('✅ Notification manager import successful')
    
    from notes.note_manager import NoteManager
    print('✅ Note manager import successful')
    
    print('🎉 All core modules loaded successfully!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Module error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Module tests failed${NC}"
    exit 1
fi

# Test database connection and schema
python3 -c "
import sys
sys.path.insert(0, 'src')

from database.models import db_manager, Document, ReadingSession, Note, Settings

try:
    session = db_manager.get_session()
    
    # Test basic queries
    doc_count = session.query(Document).count()
    session_count = session.query(ReadingSession).count()
    note_count = session.query(Note).count()
    settings_count = session.query(Settings).count()
    
    print(f'✅ Database schema test passed')
    print(f'📊 Current data: {doc_count} docs, {session_count} sessions, {note_count} notes, {settings_count} settings')
    
    session.close()
    
except Exception as e:
    print(f'❌ Database test failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database tests failed${NC}"
    exit 1
fi

# Create quick start guide
echo -e "${BLUE}📚 Creating quick start guide...${NC}"

cat > QUICK_START.md << 'EOF'
# SprintReader Quick Start Guide

## 🚀 Getting Started

### Starting SprintReader
```bash
./run_production.sh
```

### First Time Setup
1. **Open a PDF**: Ctrl+O or click "📁 Open PDF"
2. **Start Reading**: Choose your timer mode:
   - 🍅 Pomodoro (25 min) - Ctrl+P
   - ⚡ Sprint (5 min) - Ctrl+S
3. **Take Notes**: Select text in PDF to create highlights and notes
4. **Enable Focus**: Press F11 for distraction-free reading

## ⌨️ Essential Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open PDF |
| `Ctrl+P` | Start Pomodoro |
| `Ctrl+S` | Start Sprint |
| `F11` | Toggle Focus Mode |
| `Ctrl+1-4` | Switch between tabs |
| `←/→` | Navigate PDF pages |
| `Ctrl++/-` | Zoom in/out |

## 🎯 Reading Workflow

1. **Open Document**: Use Ctrl+O to open your PDF
2. **Check Time Estimate**: View in Dashboard or sidebar
3. **Choose Timer Mode**: 
   - Pomodoro for deep focus
   - Sprint for quick review
4. **Read Actively**: Highlight important text
5. **Take Notes**: Convert highlights to structured notes
6. **Track Progress**: Monitor reading speed and goals

## 📝 Note-Taking Features

- **Highlight to Note**: Select text → Create note with context
- **Topic Organization**: Notes auto-organized by topic
- **Bidirectional Links**: Use [[Note Name]] to link notes
- **Tags**: Add #tags for easy categorization
- **Search**: Ctrl+F to search across all notes
- **Export**: Export individual topics or all notes

## 📊 Analytics & Insights

- **Dashboard**: Overview of reading progress and goals
- **Time Estimation**: Smart predictions based on your reading speed
- **Reading Patterns**: Analyze your most productive times
- **Focus Analytics**: Track productivity during focus sessions
- **Goal Tracking**: Set and monitor reading goals

## 🎯 Focus Modes

| Mode | Description |
|------|-------------|
| **Minimal** | Hide sidebar only |
| **Standard** | Hide sidebar + non-essential UI |
| **Deep** | Hide everything except PDF |
| **Immersive** | Full-screen + ambient features |

## 🔧 Settings & Customization

Access via **⚙️ Settings** button or Ctrl+, (Mac)

- **Timer Durations**: Customize Pomodoro/Sprint lengths
- **Focus Preferences**: Set default focus level
- **Notifications**: Configure reading reminders
- **Theme**: Choose Light/Dark theme
- **Auto-save**: Adjust save frequency

## 💾 Data Management

### Backup Your Data
```bash
./backup_data.sh
```

### Export Notes
- Individual notes: Right-click note → Export
- All notes: Menu → File → Export → Export All Notes
- Complete backup: Menu → File → Export → Export All Data

## 🆘 Troubleshooting

### Database Issues
```bash
# Restart PostgreSQL
brew services restart postgresql

# Check connection
psql -h localhost -p 5432 -U sprintreader_user -d sprintreader_production
```

### Application Won't Start
1. Check PostgreSQL is running: `pg_isready`
2. Verify virtual environment: `source venv/bin/activate`
3. Check logs: `tail -f logs/sprintreader.log`

### Performance Issues
- Close unused applications during focus sessions
- Reduce PDF zoom level for large documents
- Clear old reading sessions via Settings

## 📞 Support

- **Documentation**: README.md
- **Logs**: Check `logs/sprintreader.log`
- **Backup**: Run `./backup_data.sh` before troubleshooting
- **Reset**: Delete `~/.sprintreader/` to reset preferences

## 🎯 Pro Tips

1. **Morning Routine**: Check Dashboard → Start with time estimates
2. **Focus Sessions**: Use Deep mode for technical documents
3. **Note-Taking**: Create notes as you read, not after
4. **Goals**: Set realistic daily reading targets
5. **Breaks**: Honor break times for better retention
6. **Analytics**: Review weekly patterns to optimize schedule

Happy Focused Reading! 📚🎯
EOF

echo -e "${GREEN}✅ Quick start guide created${NC}"

# Final setup completion
echo ""
echo -e "${PURPLE}🎉 SprintReader Production Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "   ✅ Virtual environment created and configured"
echo -e "   ✅ PostgreSQL database initialized"
echo -e "   ✅ All dependencies installed"
echo -e "   ✅ Application directories created"
echo -e "   ✅ Configuration files generated"
echo -e "   ✅ Backup system configured"
echo -e "   ✅ Production scripts created"
echo -e "   ✅ All module tests passed"
echo ""
echo -e "${GREEN}🚀 Ready to launch SprintReader!${NC}"
echo ""
echo -e "${YELLOW}Quick Start:${NC}"
echo -e "   1. Launch: ${BLUE}./run_production.sh${NC}"
echo -e "   2. Open PDF: ${BLUE}Ctrl+O${NC}"
echo -e "   3. Start timer: ${BLUE}Ctrl+P${NC} (Pomodoro) or ${BLUE}Ctrl+S${NC} (Sprint)"
echo -e "   4. Focus mode: ${BLUE}F11${NC}"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo -e "   • Quick Start: ${BLUE}QUICK_START.md${NC}"
echo -e "   • Full README: ${BLUE}README.md${NC}"
echo -e "   • Create backup: ${BLUE}./backup_data.sh${NC}"
echo ""
echo -e "${YELLOW}🎯 Key Features Enabled:${NC}"
echo -e "   📖 Smart PDF reading with time estimation"
echo -e "   ⏱️ Pomodoro and Sprint timer modes"
echo -e "   🎯 Multi-level focus modes (Minimal → Immersive)"
echo -e "   📝 Highlight-to-note functionality"
echo -e "   📊 Comprehensive reading analytics"
echo -e "   🎨 Topic-based organization"
echo -e "   🏆 Goal tracking and progress monitoring"
echo -e "   💾 Local-first data storage (privacy-focused)"
echo -e "   🔔 Smart notifications and reminders"
echo -e "   📈 Advanced productivity insights"
echo ""
echo -e "${GREEN}🎊 Happy focused reading with SprintReader!${NC}"
echo "" Deployment Script
# Final version for Mac Mini M4 deployment

set -e

echo "🚀 SprintReader Production Deployment"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo -e "${RED}❌ Please run this script from the SprintReader project directory${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Checking system requirements...${NC}"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
major_version=$(echo $python_version | cut -d'.' -f1)
minor_version=$(echo $python_version | cut -d'.' -f2)

if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 8 ]]; then
    echo -e "${RED}❌ Python 3.8+ required. Found: $python_version${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python version: $python_version${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL not found. Please install PostgreSQL first.${NC}"
    echo -e "${YELLOW}💡 On macOS: brew install postgresql${NC}"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL found${NC}"

# Check PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running. Starting it now...${NC}"
    if command -v brew &> /dev/null; then
        brew services start postgresql
        sleep 3
        if ! pg_isready -h localhost -p 5432 &> /dev/null; then
            echo -e "${RED}❌ Failed to start PostgreSQL${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Please start PostgreSQL manually${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo -e "${BLUE}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}📦 Updating pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install additional production dependencies
echo -e "${BLUE}📦 Installing production dependencies...${NC}"
pip install --upgrade \
    PyQt6==6.7.0 \
    PyMuPDF==1.24.1 \
    psycopg2-binary==2.9.9 \
    SQLAlchemy==2.0.25 \
    python-dotenv==1.0.0 \
    python-dateutil==2.8.2 \
    markdown==3.5.2 \
    python-frontmatter==1.1.0 \
    PyYAML==6.0.1

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo -e "${BLUE}⚙️ Creating environment configuration...${NC}"
    
    cat > .env << 'EOF'
# SprintReader Production