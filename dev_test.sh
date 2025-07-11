#!/bin/bash

# SprintReader - Quick Development Test
# Tests all components without launching GUI

set -e

echo "🧪 SprintReader Development Test"
echo "==============================="

source venv/bin/activate
source .env

echo "Testing core components..."

cd src && python -c "
import sys

# Test all major components
try:
    # Database
    from database.models import db_manager
    session = db_manager.get_session()
    session.close()
    print('✅ Database connection working')
    
    # PDF Handler
    from pdf_handler.pdf_handler import PDFHandler
    print('✅ PDF Handler module loaded')
    
    # UI Components (without showing GUI)
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    from ui.pdf_viewer_widget import PDFViewerWidget
    app.quit()
    print('✅ UI components loaded')
    
    print('')
    print('🎉 All components working correctly!')
    print('✅ Ready to run: ./run.sh')
    
except Exception as e:
    print(f'❌ Component test failed: {e}')
    sys.exit(1)
"
