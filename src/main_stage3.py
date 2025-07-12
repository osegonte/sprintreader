"""
SprintReader - Main Application (Stage 3)
Enhanced with timer modes, focus features, and analytics
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QMenuBar, QStatusBar, QMessageBox, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QFont
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import our modules
from database.models import db_manager
from ui.pdf_viewer_widget import PDFViewerWidget
from timer.timer_manager import TimerManager, TimerMode
from focus.focus_manager import FocusManager
from analytics.analytics_manager import AnalyticsManager
from notifications.notification_manager import NotificationManager
from estimation.time_estimator import TimeEstimator
from estimation.reading_predictor import ReadingPredictor

class SprintReaderMainWindow(QMainWindow):
    """Enhanced main application window with Stage 3 features"""
    
    def __init__(self):
        super().__init__()
        self.pdf_viewer = None
        
        # Initialize Stage 3 managers
        self.timer_manager = TimerManager()
        self.focus_manager = FocusManager()
        self.analytics_manager = AnalyticsManager()
        self.notification_manager = NotificationManager()
        
        # Initialize time estimation
        self.time_estimator = TimeEstimator()
        self.reading_predictor = ReadingPredictor()
        
        # Timer state
        self.current_timer_mode = TimerMode.REGULAR
        self.timer_active = False
        
        self.init_ui()
        self.init_database()
        self.init_menu_bar()
        self.init_stage3_toolbar()
        self.init_status_bar()
        self.init_shortcuts()
        self.connect_stage3_signals()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("SprintReader - Focused PDF Reading & Time Tracking")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Add Stage 3 timer toolbar
        self.create_timer_toolbar(main_layout)
        
        # Create and set the PDF viewer
        self.pdf_viewer = PDFViewerWidget()
        main_layout.addWidget(self.pdf_viewer)
        
        # Connect signals
        self.pdf_viewer.document_opened.connect(self.on_document_opened)
        self.pdf_viewer.page_changed.connect(self.on_page_changed)
    
    def create_timer_toolbar(self, parent_layout):
        """Create the timer and focus controls toolbar"""
        timer_layout = QHBoxLayout()
        
        # Timer mode selection
        timer_layout.addWidget(QLabel("Timer Mode:"))
        self.timer_mode_combo = QComboBox()
        self.timer_mode_combo.addItems(["Regular", "Pomodoro", "Sprint", "Custom"])
        self.timer_mode_combo.currentTextChanged.connect(self.on_timer_mode_changed)
        timer_layout.addWidget(self.timer_mode_combo)
        
        # Custom duration (only shown for custom mode)
        self.custom_duration_label = QLabel("Duration:")
        self.custom_duration_spinbox = QSpinBox()
        self.custom_duration_spinbox.setRange(1, 120)
        self.custom_duration_spinbox.setValue(25)
        self.custom_duration_spinbox.setSuffix(" min")
        timer_layout.addWidget(self.custom_duration_label)
        timer_layout.addWidget(self.custom_duration_spinbox)
        
        # Initially hide custom duration controls
        self.custom_duration_label.hide()
        self.custom_duration_spinbox.hide()
        
        timer_layout.addWidget(QLabel(" | "))
        
        # Timer controls
        self.start_timer_btn = QPushButton("🍅 Start Session")
        self.start_timer_btn.clicked.connect(self.start_timer_session)
        timer_layout.addWidget(self.start_timer_btn)
        
        self.pause_timer_btn = QPushButton("⏸️ Pause")
        self.pause_timer_btn.clicked.connect(self.pause_timer_session)
        self.pause_timer_btn.setEnabled(False)
        timer_layout.addWidget(self.pause_timer_btn)
        
        self.stop_timer_btn = QPushButton("⏹️ Stop")
        self.stop_timer_btn.clicked.connect(self.stop_timer_session)
        self.stop_timer_btn.setEnabled(False)
        timer_layout.addWidget(self.stop_timer_btn)
        
        timer_layout.addWidget(QLabel(" | "))
        
        # Timer display
        self.timer_display = QLabel("00:00")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.timer_display.setFont(font)
        timer_layout.addWidget(self.timer_display)
        
        timer_layout.addWidget(QLabel(" | "))
        
        # Focus mode toggle
        self.focus_mode_btn = QPushButton("🎯 Focus Mode")
        self.focus_mode_btn.clicked.connect(self.toggle_focus_mode)
        self.focus_mode_btn.setCheckable(True)
        timer_layout.addWidget(self.focus_mode_btn)
        
        # Stretch to center everything
        timer_layout.addStretch()
        
        # Session info
        self.session_info_label = QLabel("📚 Ready to Focus")
        timer_layout.addWidget(self.session_info_label)
        
        parent_layout.addLayout(timer_layout)
    
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
    
    def init_stage3_toolbar(self):
        """Initialize Stage 3 specific toolbar elements"""
        # Timer update
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update_timer_display)
        self.timer_update.start(1000)  # Update every second
    
    def init_menu_bar(self):
        """Initialize the menu bar with Stage 3 additions"""
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
        
        view_menu.addSeparator()
        
        focus_action = QAction('&Focus Mode', self)
        focus_action.setShortcut(QKeySequence('F11'))
        focus_action.triggered.connect(self.toggle_focus_mode)
        view_menu.addAction(focus_action)
        
        # Timer Menu (NEW)
        timer_menu = menubar.addMenu('&Timer')
        
        pomodoro_action = QAction('Start &Pomodoro', self)
        pomodoro_action.setShortcut(QKeySequence('Ctrl+P'))
        pomodoro_action.triggered.connect(lambda: self.start_specific_timer(TimerMode.POMODORO))
        timer_menu.addAction(pomodoro_action)
        
        sprint_action = QAction('Start &Sprint', self)
        sprint_action.setShortcut(QKeySequence('Ctrl+S'))
        sprint_action.triggered.connect(lambda: self.start_specific_timer(TimerMode.SPRINT))
        timer_menu.addAction(sprint_action)
        
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
        
        # Analytics Menu (NEW)
        analytics_menu = menubar.addMenu('&Analytics')
        
        daily_stats_action = QAction('&Daily Statistics', self)
        daily_stats_action.triggered.connect(self.show_daily_stats)
        analytics_menu.addAction(daily_stats_action)
        
        weekly_stats_action = QAction('&Weekly Report', self)
        weekly_stats_action.triggered.connect(self.show_weekly_stats)
        analytics_menu.addAction(weekly_stats_action)
        
        analytics_menu.addSeparator()
        
        time_estimate_action = QAction("&Time Estimates", self)
        time_estimate_action.triggered.connect(self.show_time_estimates)
        analytics_menu.addAction(time_estimate_action)
        
        completion_forecast_action = QAction("&Completion Forecast", self)
        completion_forecast_action.triggered.connect(self.show_completion_forecast)
        analytics_menu.addAction(completion_forecast_action)
        
        # Help Menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_status_bar(self):
        """Initialize the status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Choose a timer mode and open a PDF file")
    
    def init_shortcuts(self):
        """Initialize keyboard shortcuts"""
        pass
    
    def connect_stage3_signals(self):
        """Connect Stage 3 manager signals"""
        # Timer signals
        self.timer_manager.timer_started.connect(self.on_timer_started)
        self.timer_manager.timer_finished.connect(self.on_timer_finished)
        self.timer_manager.break_started.connect(self.on_break_started)
        self.timer_manager.break_finished.connect(self.on_break_finished)
        
        # Focus mode signals
        self.focus_manager.focus_mode_enabled.connect(self.on_focus_enabled)
        self.focus_manager.focus_mode_disabled.connect(self.on_focus_disabled)
        
        # Notification signals
        self.notification_manager.notification_sent.connect(self.on_notification_sent)
    
    # Stage 3 Timer Methods
    def on_timer_mode_changed(self, mode_text):
        """Handle timer mode change"""
        mode_map = {
            "Regular": TimerMode.REGULAR,
            "Pomodoro": TimerMode.POMODORO,
            "Sprint": TimerMode.SPRINT,
            "Custom": TimerMode.CUSTOM
        }
        
        self.current_timer_mode = mode_map.get(mode_text, TimerMode.REGULAR)
        
        # Show/hide custom duration controls
        is_custom = mode_text == "Custom"
        self.custom_duration_label.setVisible(is_custom)
        self.custom_duration_spinbox.setVisible(is_custom)
        
        # Update button text based on mode
        mode_icons = {
            "Regular": "📖",
            "Pomodoro": "🍅", 
            "Sprint": "⚡",
            "Custom": "⏱️"
        }
        
        icon = mode_icons.get(mode_text, "📖")
        self.start_timer_btn.setText(f"{icon} Start {mode_text}")
    
    def start_timer_session(self):
        """Start a timer session based on current mode"""
        if self.timer_active:
            return
        
        success = False
        if self.current_timer_mode == TimerMode.POMODORO:
            success = self.timer_manager.start_pomodoro()
        elif self.current_timer_mode == TimerMode.SPRINT:
            success = self.timer_manager.start_sprint()
        elif self.current_timer_mode == TimerMode.CUSTOM:
            duration = self.custom_duration_spinbox.value()
            success = self.timer_manager.start_custom(duration)
        
        if success:
            self.timer_active = True
            self.start_timer_btn.setEnabled(False)
            self.pause_timer_btn.setEnabled(True)
            self.stop_timer_btn.setEnabled(True)
    
    def start_specific_timer(self, mode: TimerMode):
        """Start a specific timer mode (for menu/shortcut actions)"""
        mode_index = {
            TimerMode.REGULAR: 0,
            TimerMode.POMODORO: 1,
            TimerMode.SPRINT: 2,
            TimerMode.CUSTOM: 3
        }
        
        self.timer_mode_combo.setCurrentIndex(mode_index.get(mode, 0))
        self.start_timer_session()
    
    def pause_timer_session(self):
        """Pause current timer session"""
        if self.timer_manager.is_running():
            self.timer_manager.pause()
            self.pause_timer_btn.setText("▶️ Resume")
        else:
            self.timer_manager.resume()
            self.pause_timer_btn.setText("⏸️ Pause")
    
    def stop_timer_session(self):
        """Stop current timer session"""
        self.timer_manager.stop()
        self.timer_active = False
        self.start_timer_btn.setEnabled(True)
        self.pause_timer_btn.setEnabled(False)
        self.stop_timer_btn.setEnabled(False)
        self.pause_timer_btn.setText("⏸️ Pause")
        self.timer_display.setText("00:00")
        self.session_info_label.setText("📚 Ready to Focus")
    
    def update_timer_display(self):
        """Update timer display every second"""
        if self.timer_manager.is_running() or self.timer_manager.get_state().name == "BREAK":
            time_str = self.timer_manager.get_formatted_time()
            self.timer_display.setText(time_str)
            
            # Update session info
            state = self.timer_manager.get_state()
            if state.name == "RUNNING":
                mode = self.timer_manager.get_current_mode().value.title()
                self.session_info_label.setText(f"🎯 {mode} Session Active")
            elif state.name == "BREAK":
                self.session_info_label.setText("☕ Break Time")
            elif state.name == "PAUSED":
                self.session_info_label.setText("⏸️ Session Paused")
    
    # Stage 3 Focus Mode Methods
    def toggle_focus_mode(self):
        """Toggle focus mode on/off"""
        self.focus_manager.toggle_focus_mode(self)
        
        # Update button state
        is_focus = self.focus_manager.is_enabled()
        self.focus_mode_btn.setChecked(is_focus)
        self.focus_mode_btn.setText("🔍 Exit Focus" if is_focus else "🎯 Focus Mode")
    
    # Stage 3 Analytics Methods  
    def show_daily_stats(self):
        """Show daily reading statistics"""
        stats = self.analytics_manager.get_daily_stats()
        
        message = f"""
📊 Daily Reading Statistics

📖 Total Reading Time: {stats.get('total_reading_time', 0)} minutes
📄 Pages Read: {stats.get('total_pages_read', 0)}
🔄 Sessions: {stats.get('session_count', 0)}
⚡ Average Speed: {stats.get('average_reading_speed', 0)} pages/min
⏱️ Longest Session: {stats.get('longest_session', 0)} minutes

Timer Mode Breakdown:
{self._format_session_types(stats.get('session_types', {}))}
        """.strip()
        
        QMessageBox.information(self, "Daily Statistics", message)
    
    def show_weekly_stats(self):
        """Show weekly reading report"""
        stats = self.analytics_manager.get_weekly_stats()
        
        message = f"""
📈 Weekly Reading Report

📖 Total Reading Time: {stats.get('total_reading_time', 0)} minutes
📄 Total Pages: {stats.get('total_pages_read', 0)}
🔄 Total Sessions: {stats.get('total_sessions', 0)}
📊 Daily Average: {stats.get('average_daily_time', 0)} min/day
🔥 Reading Streak: {stats.get('streak_days', 0)} days
🏆 Most Productive Day: {stats.get('most_productive_day', 'N/A')}
        """.strip()
        
        QMessageBox.information(self, "Weekly Report", message)
    
    def _format_session_types(self, session_types):
        """Format session types for display"""
        if not session_types:
            return "No sessions yet"
        
        formatted = []
        for session_type, count in session_types.items():
            formatted.append(f"  {session_type.title()}: {count}")
        
        return "\n".join(formatted)
    
    # Stage 3 Signal Handlers
    def on_timer_started(self, mode):
        """Handle timer started signal"""
        self.notification_manager.send_notification(
            f"🎯 {mode.title()} Started",
            "Focus session has begun. Happy reading!"
        )
    
    def on_timer_finished(self, mode):
        """Handle timer finished signal"""
        self.timer_active = False
        self.start_timer_btn.setEnabled(True)
        self.pause_timer_btn.setEnabled(False)
        self.stop_timer_btn.setEnabled(False)
        
        self.notification_manager.send_timer_notification(mode, "complete")
        
        # Show completion message
        QMessageBox.information(
            self,
            f"{mode.title()} Complete!",
            f"Great job! Your {mode} session is finished.\n\nHow did it go?"
        )
    
    def on_break_started(self, duration):
        """Handle break started signal"""
        minutes = duration // 60
        self.notification_manager.send_notification(
            "☕ Break Time!",
            f"Take a {minutes}-minute break. You've earned it!"
        )
    
    def on_break_finished(self):
        """Handle break finished signal"""
        self.timer_active = False
        self.start_timer_btn.setEnabled(True)
        self.pause_timer_btn.setEnabled(False)
        self.stop_timer_btn.setEnabled(False)
        
        self.notification_manager.send_notification(
            "⏰ Break Over",
            "Ready for another focused session?"
        )
    
    def on_focus_enabled(self):
        """Handle focus mode enabled"""
        self.status_bar.showMessage("🎯 Focus Mode Active - Minimize distractions")
    
    def on_focus_disabled(self):
        """Handle focus mode disabled"""
        self.status_bar.showMessage("🔍 Focus Mode Disabled - All controls restored")
    
    def on_notification_sent(self, message):
        """Handle notification sent signal"""
        print(f"📢 Notification: {message}")
    
    # Original Stage 2 Methods
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
        """Show about dialog with Stage 3 features"""
        QMessageBox.about(
            self,
            "About SprintReader",
            """
            <h3>SprintReader v3.0</h3>
            <p><b>Focused PDF Reading & Productivity Tool</b></p>
            
            <p><b>🎯 Stage 3 Features:</b></p>
            <ul>
            <li>🍅 Pomodoro Timer (25 min focus + breaks)</li>
            <li>⚡ Sprint Sessions (5 min quick reading)</li>
            <li>🎯 Focus Mode (distraction-free interface)</li>
            <li>📊 Enhanced Analytics (reading insights)</li>
            <li>🔔 Smart Notifications (progress alerts)</li>
            <li>🔥 Reading Streaks (habit building)</li>
            </ul>
            
            <p><b>📖 Stage 2 Foundation:</b></p>
            <ul>
            <li>📖 PDF Viewer with smooth navigation</li>
            <li>⏱️ Automatic time tracking per page</li>
            <li>📊 Reading speed calculation</li>
            <li>💾 Progress saving (local database)</li>
            <li>🔍 Zoom controls & keyboard shortcuts</li>
            </ul>
            
            <p><b>⌨️ Keyboard Shortcuts:</b></p>
            <ul>
            <li>Ctrl+O: Open PDF</li>
            <li>Ctrl+P: Start Pomodoro</li>
            <li>Ctrl+S: Start Sprint</li>
            <li>F11: Toggle Focus Mode</li>
            <li>←/→: Previous/Next Page</li>
            <li>Ctrl++/-: Zoom In/Out</li>
            </ul>
            
            <p><i>Built for focused, productive reading with local-first data storage.</i></p>
            """
        )
    
    def show_time_estimates(self):
        """Show time estimation for current document"""
        if not self.pdf_viewer.pdf_handler.document_id:
            QMessageBox.information(self, "Time Estimates", "Please open a PDF document first.")
            return
        
        estimate = self.time_estimator.estimate_document_completion(
            self.pdf_viewer.pdf_handler.document_id
        )
        
        if not estimate:
            QMessageBox.warning(self, "Time Estimates", "Unable to calculate estimates.")
            return
        
        message = f"""
📊 Smart Time Estimation

📖 Document: {estimate.get("document_title", "Unknown")}
📄 Progress: {estimate.get("current_page", 0)} / {estimate.get("total_pages", 0)} pages ({estimate.get("progress_percent", 0)}%)

⏱️ Time Estimates:
• Remaining pages: {estimate.get("remaining_pages", 0)}
• Time per page: {estimate.get("avg_time_per_page_seconds", 0):.1f} seconds
• Estimated time to finish: {estimate.get("estimated_time_remaining_formatted", "Unknown")}

📅 Completion Forecast:
• At your current pace: {estimate.get("estimated_completion_date", "Unknown")[:10] if estimate.get("estimated_completion_date") else "Unknown"}
• Confidence level: {estimate.get("confidence_level", "Unknown")}

💡 Recommendation:
{estimate.get("recommendation", "Keep reading!")}
        """.strip()
        
        QMessageBox.information(self, "📊 Time Estimates", message)
    
    def show_completion_forecast(self):
        """Show completion forecast for all documents"""
        forecast = self.time_estimator.estimate_all_documents_completion()
        
        if not forecast:
            QMessageBox.warning(self, "Completion Forecast", "Unable to generate forecast.")
            return
        
        message = f"""
🎯 Complete Reading Forecast

📚 Library Overview:
• Total documents: {forecast.get("total_documents", 0)}
• Completed: {forecast.get("completed_documents", 0)}
• Remaining: {forecast.get("remaining_documents", 0)}
• Overall progress: {forecast.get("completion_percentage", 0)}%

⏱️ Time Estimates:
• Total time remaining: {forecast.get("total_estimated_time_formatted", "Unknown")}
• Your daily average: {forecast.get("daily_average_reading_minutes", 0):.1f} minutes
• Days to complete all: {forecast.get("estimated_days_to_complete", "Unknown")}

🎯 Strategic Recommendation:
{forecast.get("overall_recommendation", "Keep up the great work!")}

💡 Tip: Check individual document estimates in the Time Estimates view.
        """.strip()
        
        QMessageBox.information(self, "🎯 Completion Forecast", message)
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop any active timers
        if self.timer_active:
            self.timer_manager.stop()
        
        # Close analytics manager
        self.analytics_manager.close()
        
        # Close time estimation managers
        self.time_estimator.close()
        self.reading_predictor.close()
        
        # The PDF viewer will handle saving its own state
        print("👋 SprintReader (Stage 3) closing...")
        event.accept()

def main():
    """Main application entry point"""
    print("🚀 Starting SprintReader Stage 3...")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("SprintReader")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("SprintReader")
    
    # Set application style
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform look
    
    # Create main window
    window = SprintReaderMainWindow()
    window.show()
    
    print("✅ SprintReader Stage 3 launched successfully!")
    print("🎯 Enhanced Features Available:")
    print("   🍅 Pomodoro Timer (Ctrl+P)")
    print("   ⚡ Sprint Sessions (Ctrl+S)")
    print("   🎯 Focus Mode (F11)")
    print("   📊 Analytics (Menu > Analytics)")
    print("   🔔 Smart Notifications")
    print("")
    print("📖 Use Ctrl+O to open a PDF file")
    print("⏹️  Press Ctrl+C in terminal or close window to quit")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()