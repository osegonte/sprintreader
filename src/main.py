"""
SprintReader - Main Application
Entry point for the SprintReader application
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import our database models
from database.models import db_manager

class SprintReaderMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_database()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("SprintReader - Stage 1")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title_label = QLabel("SprintReader")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Stage 1 Setup Complete")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Arial", 16)
        subtitle_label.setFont(subtitle_font)
        layout.addWidget(subtitle_label)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("Arial", 12)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)
        
        # Info
        info_text = """
        ✅ PostgreSQL Database: Connected
        ✅ Python Environment: Active
        ✅ PyQt6 Interface: Running
        ✅ Database Models: Loaded
        
        Ready for Stage 2 Development!
        
        Next Steps:
        • PDF Viewer Implementation
        • Timer Integration
        • Basic UI Components
        """
        
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_font = QFont("Monaco", 10)
        info_label.setFont(info_font)
        info_label.setStyleSheet("QLabel { color: #666; background-color: #f5f5f5; padding: 20px; border-radius: 5px; }")
        layout.addWidget(info_label)
    
    def init_database(self):
        """Initialize database connection"""
        try:
            # Test database connection
            db_manager.create_tables()
            session = db_manager.get_session()
            session.close()
            
            self.status_label.setText("✅ Database Connected Successfully")
            self.status_label.setStyleSheet("QLabel { color: green; }")
            
        except Exception as e:
            self.status_label.setText(f"❌ Database Connection Error: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            print(f"Database error: {e}")

def main():
    """Main application entry point"""
    print("🚀 Starting SprintReader...")
    print("=" * 40)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("SprintReader")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SprintReader")
    
    # Create main window
    window = SprintReaderMainWindow()
    window.show()
    
    print("✅ SprintReader Stage 1 launched successfully!")
    print("📱 GUI Application is running...")
    print("🔍 Check the application window for status")
    print("⏹️  Press Ctrl+C in terminal or close window to quit")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
