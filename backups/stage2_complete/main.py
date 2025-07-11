"""
SprintReader - Main Application (Stage 2)
Entry point with PDF viewer functionality
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QMenuBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import our modules
from database.models import db_manager
from ui.pdf_viewer_widget import PDFViewerWidget

class SprintReaderMainWindow(QMainWindow):
    """Main application window with PDF viewer"""
    
    def __init__(self):
        super().__init__()
        self.pdf_viewer = None
        self.init_ui()
        self.init_database()
        self.init_menu_bar()
        self.init_status_bar()
        self.init_shortcuts()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("SprintReader - PDF Reading & Time Tracking")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create and set the PDF viewer as central widget
        self.pdf_viewer = PDFViewerWidget()
        self.setCentralWidget(self.pdf_viewer)
        
        # Connect signals
        self.pdf_viewer.document_opened.connect(self.on_document_opened)
        self.pdf_viewer.page_changed.connect(self.on_page_changed)
    
    def init_database(self):
        """Initialize database connection"""
        try:
            # Test database connection
            db_manager.create_tables()
            session = db_manager.get_session()
            session.close()
            
            print("✅ Database Connected Successfully")
            
        except Exception as e:
            print(f"❌ Database Connection Error: {str(e)}")
            QMessageBox.critical(
                self, 
                "Database Error", 
                f"Failed to connect to database:\n{str(e)}\n\nPlease check your PostgreSQL connection."
            )
    
    def init_menu_bar(self):
        """Initialize the menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open PDF...', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip('Open a PDF file')
        open_action.triggered.connect(self.pdf_viewer.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu('&View')
        
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.pdf_viewer.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.pdf_viewer.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # Navigation Menu
        nav_menu = menubar.addMenu('&Navigation')
        
        prev_page_action = QAction('&Previous Page', self)
        prev_page_action.setShortcut(QKeySequence('Left'))
        prev_page_action.triggered.connect(self.pdf_viewer.previous_page)
        nav_menu.addAction(prev_page_action)
        
        next_page_action = QAction('&Next Page', self)
        next_page_action.setShortcut(QKeySequence('Right'))
        next_page_action.triggered.connect(self.pdf_viewer.next_page)
        nav_menu.addAction(next_page_action)
        
        # Help Menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_status_bar(self):
        """Initialize the status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Open a PDF file to start reading")
    
    def init_shortcuts(self):
        """Initialize keyboard shortcuts"""
        # These are additional shortcuts beyond menu items
        pass
    
    def on_document_opened(self, filepath: str):
        """Handle document opened event"""
        filename = os.path.basename(filepath)
        self.status_bar.showMessage(f"Opened: {filename}")
        self.setWindowTitle(f"SprintReader - {filename}")
    
    def on_page_changed(self, page_num: int):
        """Handle page change event"""
        if self.pdf_viewer.pdf_handler.total_pages > 0:
            progress = (page_num / self.pdf_viewer.pdf_handler.total_pages) * 100
            self.status_bar.showMessage(
                f"Page {page_num} of {self.pdf_viewer.pdf_handler.total_pages} ({progress:.1f}%)"
            )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SprintReader",
            """
            <h3>SprintReader v2.0</h3>
            <p><b>Focused PDF Reading & Time Tracking</b></p>
            
            <p>SprintReader helps you read PDFs more efficiently by tracking your reading time, 
            calculating reading speed, and helping you set realistic study goals.</p>
            
            <p><b>Stage 2 Features:</b></p>
            <ul>
            <li>📖 PDF Viewer with smooth navigation</li>
            <li>⏱️ Automatic time tracking per page</li>
            <li>📊 Reading speed calculation</li>
            <li>💾 Progress saving (local database)</li>
            <li>🔍 Zoom controls</li>
            <li>⌨️ Keyboard shortcuts</li>
            </ul>
            
            <p><b>Keyboard Shortcuts:</b></p>
            <ul>
            <li>Ctrl+O: Open PDF</li>
            <li>Ctrl++: Zoom In</li>
            <li>Ctrl+-: Zoom Out</li>
            <li>←/→: Previous/Next Page</li>
            <li>Ctrl+Q: Quit</li>
            </ul>
            
            <p><i>Built with PyQt6 and PostgreSQL for fast, local-first reading.</i></p>
            """
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        # The PDF viewer will handle saving its own state
        print("👋 SprintReader closing...")
        event.accept()

def main():
    """Main application entry point"""
    print("🚀 Starting SprintReader Stage 2...")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("SprintReader")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("SprintReader")
    
    # Set application style
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform look
    
    # Create main window
    window = SprintReaderMainWindow()
    window.show()
    
    print("✅ SprintReader Stage 2 launched successfully!")
    print("📱 PDF Viewer Application is running...")
    print("📖 Use Ctrl+O to open a PDF file")
    print("⏹️  Press Ctrl+C in terminal or close window to quit")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()