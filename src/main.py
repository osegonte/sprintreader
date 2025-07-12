#!/usr/bin/env python3
"""
SprintReader - Final Production Version
A comprehensive PDF reading and productivity application with smart time estimation,
goal tracking, note-taking, and focus management.

Author: SprintReader Team
Version: 1.0.0 (Production Release)
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QTabWidget, QStatusBar, QMenuBar,
    QMessageBox, QSystemTrayIcon, QMenu, QProgressBar, QFrame,
    QToolBar, QFileDialog, QDialog, QFormLayout, QSpinBox, QCheckBox,
    QComboBox, QTextEdit, QDialogButtonBox, QGroupBox, QGridLayout,
    QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QKeySequence, QFont, QIcon, QPixmap, QPalette, QColor
from dotenv import load_dotenv

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables from parent directory
env_path = current_dir.parent / '.env'
load_dotenv(env_path)

# Create logs directory in parent directory if it doesn't exist
logs_dir = current_dir.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Import application modules
try:
    from database.models import db_manager, initialize_stage5_settings
    from ui.pdf_viewer import PDFViewerWidget
    from timer.timer_manager import TimerManager, TimerMode, TimerState
    from analytics.analytics_manager import AnalyticsManager
    from estimation.time_estimator import TimeEstimator
    from estimation.reading_predictor import ReadingPredictor
    from focus.focus_manager import FocusManager, FocusLevel
    from notifications.notification_manager import NotificationManager
    from notes.note_manager import NoteManager
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed and the database is initialized.")
    sys.exit(1)

# Configure logging with correct path
log_file = logs_dir / 'sprintreader.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DashboardWidget(QWidget):
    """Enhanced dashboard widget showing comprehensive overview"""
    
    def __init__(self, analytics_manager, time_estimator, goal_manager=None):
        super().__init__()
        self.analytics_manager = analytics_manager
        self.time_estimator = time_estimator
        self.goal_manager = goal_manager
        
        self.init_ui()
        self.setup_refresh_timer()
        self.refresh_dashboard()
    
    def init_ui(self):
        """Initialize dashboard UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 SprintReader Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Last updated
        self.last_updated_label = QLabel(f"Updated: {datetime.now().strftime('%H:%M')}")
        self.last_updated_label.setStyleSheet("color: #666; font-style: italic;")
        header_layout.addWidget(self.last_updated_label)
        
        layout.addLayout(header_layout)
        
        # Create scroll area for dashboard content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Dashboard content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Today's overview
        self.create_todays_overview(content_layout)
        
        # Quick stats grid
        self.create_quick_stats_grid(content_layout)
        
        # Recent activity
        self.create_recent_activity(content_layout)
        
        # Time estimates
        self.create_time_estimates(content_layout)
        
        # Productivity insights
        self.create_productivity_insights(content_layout)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
    
    def create_todays_overview(self, parent_layout):
        """Create today's overview section"""
        group = QGroupBox("📅 Today's Overview")
        layout = QVBoxLayout(group)
        
        # Progress bar for daily goal
        self.daily_progress = QProgressBar()
        self.daily_progress.setTextVisible(True)
        layout.addWidget(self.daily_progress)
        
        # Today's stats grid
        stats_layout = QGridLayout()
        
        self.reading_time_label = QLabel("⏱️ 0min")
        self.reading_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.reading_time_label, 0, 0)
        
        self.pages_read_label = QLabel("📄 0 pages")
        self.pages_read_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.pages_read_label, 0, 1)
        
        self.sessions_label = QLabel("🎯 0 sessions")
        self.sessions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.sessions_label, 0, 2)
        
        self.streak_label = QLabel("🔥 0 day streak")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.streak_label, 0, 3)
        
        layout.addLayout(stats_layout)
        parent_layout.addWidget(group)
    
    def create_quick_stats_grid(self, parent_layout):
        """Create quick stats grid"""
        group = QGroupBox("📈 Quick Stats")
        grid_layout = QGridLayout(group)
        
        # Weekly overview
        self.weekly_stats = QTextEdit()
        self.weekly_stats.setMaximumHeight(100)
        self.weekly_stats.setReadOnly(True)
        grid_layout.addWidget(QLabel("This Week:"), 0, 0)
        grid_layout.addWidget(self.weekly_stats, 0, 1)
        
        # Average reading speed
        self.speed_label = QLabel("📊 Calculating...")
        grid_layout.addWidget(QLabel("Reading Speed:"), 1, 0)
        grid_layout.addWidget(self.speed_label, 1, 1)
        
        # Favorite reading time
        self.peak_time_label = QLabel("🕐 Analyzing...")
        grid_layout.addWidget(QLabel("Peak Time:"), 2, 0)
        grid_layout.addWidget(self.peak_time_label, 2, 1)
        
        parent_layout.addWidget(group)
    
    def create_recent_activity(self, parent_layout):
        """Create recent activity section"""
        group = QGroupBox("📚 Recent Activity")
        layout = QVBoxLayout(group)
        
        self.recent_activity_text = QTextEdit()
        self.recent_activity_text.setMaximumHeight(120)
        self.recent_activity_text.setReadOnly(True)
        layout.addWidget(self.recent_activity_text)
        
        parent_layout.addWidget(group)
    
    def create_time_estimates(self, parent_layout):
        """Create time estimates section"""
        group = QGroupBox("⏱️ Smart Time Estimates")
        layout = QVBoxLayout(group)
        
        self.estimates_text = QTextEdit()
        self.estimates_text.setMaximumHeight(100)
        self.estimates_text.setReadOnly(True)
        self.estimates_text.setStyleSheet("""
            QTextEdit {
                background-color: #f0f8ff;
                border: 1px solid #4169e1;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.estimates_text)
        
        parent_layout.addWidget(group)
    
    def create_productivity_insights(self, parent_layout):
        """Create productivity insights section"""
        group = QGroupBox("💡 Productivity Insights")
        layout = QVBoxLayout(group)
        
        self.insights_text = QTextEdit()
        self.insights_text.setMaximumHeight(120)
        self.insights_text.setReadOnly(True)
        layout.addWidget(self.insights_text)
        
        parent_layout.addWidget(group)
    
    def setup_refresh_timer(self):
        """Setup timer to refresh dashboard"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        try:
            # Get today's stats
            today_stats = self.analytics_manager.get_daily_stats()
            
            # Update today's overview
            self.reading_time_label.setText(f"⏱️ {today_stats.get('total_reading_time', 0):.0f}min")
            self.pages_read_label.setText(f"📄 {today_stats.get('total_pages_read', 0)} pages")
            self.sessions_label.setText(f"🎯 {today_stats.get('session_count', 0)} sessions")
            
            # Update daily progress (assuming 60min daily goal)
            daily_goal = 60  # minutes
            progress = min(100, (today_stats.get('total_reading_time', 0) / daily_goal) * 100)
            self.daily_progress.setValue(int(progress))
            self.daily_progress.setFormat(f"{today_stats.get('total_reading_time', 0):.0f} / {daily_goal} min ({progress:.0f}%)")
            
            # Get weekly stats
            weekly_stats = self.analytics_manager.get_weekly_stats()
            weekly_text = f"""
Total Time: {weekly_stats.get('total_reading_time', 0):.0f} minutes
Total Pages: {weekly_stats.get('total_pages_read', 0)}
Sessions: {weekly_stats.get('total_sessions', 0)}
Avg Daily: {weekly_stats.get('average_daily_time', 0):.0f} min
            """.strip()
            self.weekly_stats.setText(weekly_text)
            
            # Update reading speed
            avg_speed = today_stats.get('average_reading_speed', 0)
            if avg_speed > 0:
                self.speed_label.setText(f"📊 {avg_speed:.1f} pages/min")
            else:
                self.speed_label.setText("📊 No data yet")
            
            # Most productive time
            most_productive = weekly_stats.get('most_productive_day', 'Unknown')
            self.peak_time_label.setText(f"🕐 {most_productive}")
            
            # Recent activity
            self.update_recent_activity()
            
            # Time estimates
            self.update_time_estimates()
            
            # Productivity insights
            self.update_productivity_insights()
            
            # Update timestamp
            self.last_updated_label.setText(f"Updated: {datetime.now().strftime('%H:%M')}")
            
        except Exception as e:
            logger.error(f"Error refreshing dashboard: {e}")
    
    def update_recent_activity(self):
        """Update recent activity display"""
        try:
            activity_text = """
📖 Welcome to SprintReader!
🎯 Ready to start your first reading session
📝 Open a PDF to begin taking notes
🏆 Build your reading streak!
            """.strip()
            self.recent_activity_text.setText(activity_text)
        except Exception as e:
            self.recent_activity_text.setText("Activity data temporarily unavailable")
    
    def update_time_estimates(self):
        """Update time estimates display"""
        try:
            estimates_text = """
📚 Open a document to see time estimates
📈 Reading speed will be calculated automatically
🎯 Smart predictions based on your reading pace
⏰ Completion forecasts will appear here
            """.strip()
            self.estimates_text.setText(estimates_text)
        except Exception as e:
            self.estimates_text.setText("Estimates will appear after reading sessions")
    
    def update_productivity_insights(self):
        """Update productivity insights"""
        try:
            insights_text = """
💡 Productivity insights will develop as you read
🎯 Try different timer modes to find what works best
📊 Your reading patterns will be analyzed over time
🔄 Check back after a few reading sessions for personalized tips
            """.strip()
            self.insights_text.setText(insights_text)
        except Exception as e:
            self.insights_text.setText("Insights will develop as you use SprintReader")

class SettingsDialog(QDialog):
    """Enhanced settings dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SprintReader Settings")
        self.setModal(True)
        self.resize(500, 600)
        
        self.settings = QSettings('SprintReader', 'Main')
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """Initialize settings UI"""
        layout = QVBoxLayout(self)
        
        # Create tabs for different setting categories
        tabs = QTabWidget()
        
        # General settings
        general_tab = self.create_general_settings()
        tabs.addTab(general_tab, "⚙️ General")
        
        # Timer settings
        timer_tab = self.create_timer_settings()
        tabs.addTab(timer_tab, "⏱️ Timer")
        
        # Focus settings
        focus_tab = self.create_focus_settings()
        tabs.addTab(focus_tab, "🎯 Focus")
        
        # Notifications settings
        notifications_tab = self.create_notifications_settings()
        tabs.addTab(notifications_tab, "🔔 Notifications")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def create_general_settings(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        layout.addRow("Theme:", self.theme_combo)
        
        # Default session duration
        self.default_duration_spin = QSpinBox()
        self.default_duration_spin.setRange(5, 120)
        self.default_duration_spin.setSuffix(" minutes")
        layout.addRow("Default Session:", self.default_duration_spin)
        
        # Auto-save interval
        self.autosave_spin = QSpinBox()
        self.autosave_spin.setRange(10, 300)
        self.autosave_spin.setSuffix(" seconds")
        layout.addRow("Auto-save Interval:", self.autosave_spin)
        
        # Startup options
        self.startup_restore_check = QCheckBox("Restore last document on startup")
        layout.addRow("Startup:", self.startup_restore_check)
        
        return widget
    
    def create_timer_settings(self):
        """Create timer settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Pomodoro duration
        self.pomodoro_spin = QSpinBox()
        self.pomodoro_spin.setRange(15, 60)
        self.pomodoro_spin.setSuffix(" minutes")
        layout.addRow("Pomodoro Duration:", self.pomodoro_spin)
        
        # Break duration
        self.break_spin = QSpinBox()
        self.break_spin.setRange(3, 15)
        self.break_spin.setSuffix(" minutes")
        layout.addRow("Short Break:", self.break_spin)
        
        # Sprint duration
        self.sprint_spin = QSpinBox()
        self.sprint_spin.setRange(3, 10)
        self.sprint_spin.setSuffix(" minutes")
        layout.addRow("Sprint Duration:", self.sprint_spin)
        
        # Auto-start breaks
        self.auto_break_check = QCheckBox("Automatically start breaks")
        layout.addRow("Auto-breaks:", self.auto_break_check)
        
        return widget
    
    def create_focus_settings(self):
        """Create focus settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Default focus level
        self.focus_level_combo = QComboBox()
        self.focus_level_combo.addItems(["Minimal", "Standard", "Deep", "Immersive"])
        layout.addRow("Default Focus Level:", self.focus_level_combo)
        
        # Hide elements
        self.hide_sidebar_check = QCheckBox("Hide sidebar in focus mode")
        layout.addRow("Interface:", self.hide_sidebar_check)
        
        self.hide_statusbar_check = QCheckBox("Hide status bar in focus mode")
        layout.addRow("", self.hide_statusbar_check)
        
        return widget
    
    def create_notifications_settings(self):
        """Create notifications settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Enable notifications
        self.notifications_enabled_check = QCheckBox("Enable notifications")
        layout.addRow("General:", self.notifications_enabled_check)
        
        # Session complete notifications
        self.session_complete_check = QCheckBox("Session completion alerts")
        layout.addRow("Sessions:", self.session_complete_check)
        
        # Goal reminders
        self.goal_reminders_check = QCheckBox("Daily goal reminders")
        layout.addRow("Goals:", self.goal_reminders_check)
        
        # Break reminders
        self.break_reminders_check = QCheckBox("Break time reminders")
        layout.addRow("Breaks:", self.break_reminders_check)
        
        return widget
    
    def load_current_settings(self):
        """Load current settings from storage"""
        # Load general settings
        self.theme_combo.setCurrentText(self.settings.value('theme', 'Light'))
        self.default_duration_spin.setValue(self.settings.value('default_duration', 25, type=int))
        self.autosave_spin.setValue(self.settings.value('autosave_interval', 30, type=int))
        self.startup_restore_check.setChecked(self.settings.value('startup_restore', True, type=bool))
        
        # Load timer settings
        self.pomodoro_spin.setValue(self.settings.value('pomodoro_duration', 25, type=int))
        self.break_spin.setValue(self.settings.value('break_duration', 5, type=int))
        self.sprint_spin.setValue(self.settings.value('sprint_duration', 5, type=int))
        self.auto_break_check.setChecked(self.settings.value('auto_break', True, type=bool))
        
        # Load focus settings
        self.focus_level_combo.setCurrentText(self.settings.value('focus_level', 'Standard'))
        self.hide_sidebar_check.setChecked(self.settings.value('hide_sidebar', True, type=bool))
        self.hide_statusbar_check.setChecked(self.settings.value('hide_statusbar', True, type=bool))
        
        # Load notification settings
        self.notifications_enabled_check.setChecked(self.settings.value('notifications_enabled', True, type=bool))
        self.session_complete_check.setChecked(self.settings.value('session_complete_notifications', True, type=bool))
        self.goal_reminders_check.setChecked(self.settings.value('goal_reminders', True, type=bool))
        self.break_reminders_check.setChecked(self.settings.value('break_reminders', True, type=bool))
    
    def save_settings(self):
        """Save all settings"""
        # Save general settings
        self.settings.setValue('theme', self.theme_combo.currentText())
        self.settings.setValue('default_duration', self.default_duration_spin.value())
        self.settings.setValue('autosave_interval', self.autosave_spin.value())
        self.settings.setValue('startup_restore', self.startup_restore_check.isChecked())
        
        # Save timer settings
        self.settings.setValue('pomodoro_duration', self.pomodoro_spin.value())
        self.settings.setValue('break_duration', self.break_spin.value())
        self.settings.setValue('sprint_duration', self.sprint_spin.value())
        self.settings.setValue('auto_break', self.auto_break_check.isChecked())
        
        # Save focus settings
        self.settings.setValue('focus_level', self.focus_level_combo.currentText())
        self.settings.setValue('hide_sidebar', self.hide_sidebar_check.isChecked())
        self.settings.setValue('hide_statusbar', self.hide_statusbar_check.isChecked())
        
        # Save notification settings
        self.settings.setValue('notifications_enabled', self.notifications_enabled_check.isChecked())
        self.settings.setValue('session_complete_notifications', self.session_complete_check.isChecked())
        self.settings.setValue('goal_reminders', self.goal_reminders_check.isChecked())
        self.settings.setValue('break_reminders', self.break_reminders_check.isChecked())
        
        self.accept()

class SprintReaderMainWindow(QMainWindow):
    """Final production main window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.analytics_manager = AnalyticsManager()
        self.time_estimator = TimeEstimator()
        self.reading_predictor = ReadingPredictor()
        self.timer_manager = TimerManager()
        self.focus_manager = FocusManager()
        self.notification_manager = NotificationManager()
        self.note_manager = NoteManager()
        
        # Settings
        self.settings = QSettings('SprintReader', 'Main')
        
        # Current session state
        self.current_session_active = False
        self.focus_mode_active = False
        
        # Setup window
        self.init_ui()
        self.setup_timers()
        self.connect_signals()
        self.restore_window_state()
        
        logger.info("SprintReader main window initialized")
    
    def init_ui(self):
        """Initialize the main user interface"""
        self.setWindowTitle("SprintReader - Focused PDF Reading & Productivity")
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create status bar
        self.create_status_bar()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Apply initial theme
        self.apply_theme()
    
    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        # File actions
        open_action = QAction("📁 Open PDF", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # Timer controls
        self.pomodoro_btn = QPushButton("🍅 Pomodoro")
        self.pomodoro_btn.clicked.connect(lambda: self.start_timer('pomodoro'))
        toolbar.addWidget(self.pomodoro_btn)
        
        self.sprint_btn = QPushButton("⚡ Sprint")
        self.sprint_btn.clicked.connect(lambda: self.start_timer('sprint'))
        toolbar.addWidget(self.sprint_btn)
        
        self.timer_display = QLabel("⏱️ Ready")
        self.timer_display.setStyleSheet("font-weight: bold; color: #4169e1; padding: 8px;")
        toolbar.addWidget(self.timer_display)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.toggle_timer)
        self.pause_btn.setEnabled(False)
        toolbar.addWidget(self.pause_btn)
        
        toolbar.addSeparator()
        
        # Focus mode
        self.focus_btn = QPushButton("🎯 Focus Mode")
        self.focus_btn.setCheckable(True)
        self.focus_btn.toggled.connect(self.toggle_focus_mode)
        toolbar.addWidget(self.focus_btn)
        
        toolbar.addSeparator()
        
        # Quick actions
        self.quick_note_btn = QPushButton("📝 Quick Note")
        self.quick_note_btn.clicked.connect(self.add_quick_note)
        self.quick_note_btn.setEnabled(False)
        toolbar.addWidget(self.quick_note_btn)
        
        toolbar.addSeparator()
        
        # Settings
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_btn)
    
    def create_main_content(self, parent_layout):
        """Create the main content area with tabs"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Dashboard tab
        self.dashboard = DashboardWidget(
            self.analytics_manager, 
            self.time_estimator
        )
        self.tab_widget.addTab(self.dashboard, "📊 Dashboard")
        
        # PDF Reader tab
        self.pdf_viewer = PDFViewerWidget()
        self.tab_widget.addTab(self.pdf_viewer, "📖 Reader")
        
        # Analytics tab
        self.create_analytics_tab()
        
        # Notes tab
        self.create_notes_tab()
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_analytics_tab(self):
        """Create analytics tab"""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Analytics header
        header_layout = QHBoxLayout()
        
        title = QLabel("📈 Reading Analytics & Insights")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Create analytics content area
        analytics_scroll = QScrollArea()
        analytics_scroll.setWidgetResizable(True)
        
        analytics_content = QWidget()
        analytics_content_layout = QVBoxLayout(analytics_content)
        
        # Reading trends section
        trends_group = QGroupBox("📈 Reading Trends")
        trends_layout = QVBoxLayout(trends_group)
        
        self.trends_text = QTextEdit()
        self.trends_text.setMaximumHeight(150)
        self.trends_text.setReadOnly(True)
        self.trends_text.setText("Analytics will be available after several reading sessions...")
        trends_layout.addWidget(self.trends_text)
        
        analytics_content_layout.addWidget(trends_group)
        
        analytics_content_layout.addStretch()
        analytics_scroll.setWidget(analytics_content)
        layout.addWidget(analytics_scroll)
        
        self.tab_widget.addTab(analytics_widget, "📈 Analytics")
    
    def create_notes_tab(self):
        """Create notes management tab"""
        notes_widget = QWidget()
        layout = QVBoxLayout(notes_widget)
        
        # Notes header
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 Notes & Knowledge Base")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Notes content
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setText("Your notes will appear here once you start highlighting text in PDFs...")
        layout.addWidget(self.notes_text)
        
        self.tab_widget.addTab(notes_widget, "📝 Notes")
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Current status
        self.status_label = QLabel("Ready to start reading")
        self.status_bar.addWidget(self.status_label)
        
        self.status_bar.addPermanentWidget(QLabel(" | "))
        
        # Session info
        self.session_info_label = QLabel("No active session")
        self.status_bar.addPermanentWidget(self.session_info_label)
        
        self.status_bar.addPermanentWidget(QLabel(" | "))
        
        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Version info
        version_label = QLabel("SprintReader v1.0.0")
        version_label.setStyleSheet("color: #666; font-style: italic;")
        self.status_bar.addPermanentWidget(version_label)
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open PDF
        open_action = QAction('&Open PDF...', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Quit
        quit_action = QAction('&Quit', self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Session menu
        session_menu = menubar.addMenu('&Session')
        
        # Timer actions
        pomodoro_action = QAction('🍅 Start &Pomodoro', self)
        pomodoro_action.setShortcut(QKeySequence('Ctrl+P'))
        pomodoro_action.triggered.connect(lambda: self.start_timer('pomodoro'))
        session_menu.addAction(pomodoro_action)
        
        sprint_action = QAction('⚡ Start &Sprint', self)
        sprint_action.setShortcut(QKeySequence('Ctrl+S'))
        sprint_action.triggered.connect(lambda: self.start_timer('sprint'))
        session_menu.addAction(sprint_action)
        
        session_menu.addSeparator()
        
        # Focus mode
        focus_action = QAction('🎯 &Focus Mode', self)
        focus_action.setShortcut(QKeySequence('F11'))
        focus_action.setCheckable(True)
        focus_action.toggled.connect(self.toggle_focus_mode)
        session_menu.addAction(focus_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Tab navigation
        dashboard_action = QAction('📊 &Dashboard', self)
        dashboard_action.setShortcut(QKeySequence('Ctrl+1'))
        dashboard_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(dashboard_action)
        
        reader_action = QAction('📖 &Reader', self)
        reader_action.setShortcut(QKeySequence('Ctrl+2'))
        reader_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(reader_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        # Settings
        settings_action = QAction('⚙️ &Settings...', self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About
        about_action = QAction('ℹ️ About SprintReader', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_timers(self):
        """Setup various application timers"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
        
        # Auto-save timer
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.auto_save)
        autosave_interval = self.settings.value('autosave_interval', 30, type=int) * 1000
        self.autosave_timer.start(autosave_interval)
    
    def connect_signals(self):
        """Connect all application signals"""
        # Timer manager signals
        self.timer_manager.timer_started.connect(self.on_timer_started)
        self.timer_manager.timer_finished.connect(self.on_timer_finished)
        self.timer_manager.timer_paused.connect(self.on_timer_paused)
        self.timer_manager.timer_resumed.connect(self.on_timer_resumed)
        self.timer_manager.time_updated.connect(self.on_timer_updated)
        
        # PDF viewer signals
        self.pdf_viewer.document_opened.connect(self.on_document_opened)
        self.pdf_viewer.page_changed.connect(self.on_page_changed)
        self.pdf_viewer.note_created.connect(self.on_note_created)
    
    def apply_theme(self):
        """Apply the selected theme"""
        theme = self.settings.value('theme', 'Light')
        
        if theme == 'Dark':
            # Apply dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #3b3b3b;
                }
                QTabBar::tab {
                    background-color: #404040;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #7E22CE;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    margin: 10px 0px;
                    padding-top: 10px;
                }
            """)
        else:
            # Apply light theme (default)
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                    color: #000000;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    padding: 8px 16px;
                    margin: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #7E22CE;
                    color: white;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    margin: 10px 0px;
                    padding-top: 10px;
                }
            """)
    
    # Timer management methods
    def start_timer(self, mode):
        """Start a timer session"""
        try:
            if mode == 'pomodoro':
                success = self.timer_manager.start_pomodoro()
            elif mode == 'sprint':
                success = self.timer_manager.start_sprint()
            else:
                # Custom timer
                duration = self.settings.value('default_duration', 25, type=int)
                success = self.timer_manager.start_custom(duration)
            
            if success:
                self.current_session_active = True
                self.update_timer_buttons()
                logger.info(f"Started {mode} timer session")
            else:
                QMessageBox.warning(self, "Timer Error", "Could not start timer. Another session may be active.")
        
        except Exception as e:
            logger.error(f"Error starting timer: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start timer: {str(e)}")
    
    def toggle_timer(self):
        """Toggle timer pause/resume"""
        try:
            if self.timer_manager.get_state() == TimerState.RUNNING:
                self.timer_manager.pause()
            elif self.timer_manager.get_state() == TimerState.PAUSED:
                self.timer_manager.resume()
            
            self.update_timer_buttons()
        
        except Exception as e:
            logger.error(f"Error toggling timer: {e}")
    
    def stop_timer(self):
        """Stop current timer"""
        try:
            self.timer_manager.stop()
            self.current_session_active = False
            self.update_timer_buttons()
            logger.info("Timer stopped")
        
        except Exception as e:
            logger.error(f"Error stopping timer: {e}")
    
    def update_timer_buttons(self):
        """Update timer button states"""
        state = self.timer_manager.get_state()
        
        # Enable/disable timer start buttons
        timer_stopped = (state == TimerState.STOPPED)
        self.pomodoro_btn.setEnabled(timer_stopped)
        self.sprint_btn.setEnabled(timer_stopped)
        
        # Update pause/resume button
        if state == TimerState.RUNNING:
            self.pause_btn.setText("⏸️ Pause")
            self.pause_btn.setEnabled(True)
        elif state == TimerState.PAUSED:
            self.pause_btn.setText("▶️ Resume")
            self.pause_btn.setEnabled(True)
        else:
            self.pause_btn.setText("⏸️ Pause")
            self.pause_btn.setEnabled(False)
    
    # Focus mode methods
    def toggle_focus_mode(self, enabled=None):
        """Toggle focus mode"""
        try:
            if enabled is None:
                enabled = not self.focus_mode_active
            
            if enabled:
                # Simple focus mode - hide some UI elements
                self.focus_mode_active = True
                self.focus_btn.setText("🎯 Exit Focus")
                self.status_label.setText("Focus Mode Active")
                logger.info("Focus mode enabled")
            else:
                self.focus_mode_active = False
                self.focus_btn.setText("🎯 Focus Mode")
                self.status_label.setText("Focus mode disabled")
                logger.info("Focus mode disabled")
            
            self.focus_btn.setChecked(enabled)
        
        except Exception as e:
            logger.error(f"Error toggling focus mode: {e}")
            QMessageBox.critical(self, "Focus Mode Error", f"Failed to toggle focus mode: {str(e)}")
    
    # File operations
    def open_pdf(self):
        """Open PDF file dialog"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open PDF File",
                "",
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if file_path:
                # Switch to reader tab
                self.tab_widget.setCurrentIndex(1)
                
                # Load PDF in viewer
                self.pdf_viewer.load_pdf(file_path)
                
                # Enable note button
                self.quick_note_btn.setEnabled(True)
                
                logger.info(f"Opened PDF: {file_path}")
        
        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            QMessageBox.critical(self, "File Error", f"Failed to open PDF: {str(e)}")
    
    # Notes operations
    def add_quick_note(self):
        """Add a quick note"""
        try:
            self.pdf_viewer.add_quick_note()
        except Exception as e:
            logger.error(f"Error adding quick note: {e}")
            QMessageBox.critical(self, "Note Error", f"Failed to add note: {str(e)}")
    
    # Settings and preferences
    def show_settings(self):
        """Show settings dialog"""
        try:
            dialog = SettingsDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Apply new settings
                self.apply_theme()
                
                # Update timer settings
                self.timer_manager.work_duration = self.settings.value('pomodoro_duration', 25, type=int) * 60
                self.timer_manager.break_duration = self.settings.value('break_duration', 5, type=int) * 60
                self.timer_manager.sprint_duration = self.settings.value('sprint_duration', 5, type=int) * 60
                
                # Update autosave timer
                autosave_interval = self.settings.value('autosave_interval', 30, type=int) * 1000
                self.autosave_timer.start(autosave_interval)
                
                self.status_label.setText("Settings updated successfully")
                logger.info("Settings updated")
        
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
            QMessageBox.critical(self, "Settings Error", f"Failed to open settings: {str(e)}")
    
    # Help and about
    def show_about(self):
        """Show about dialog"""
        about_text = """
📖 SprintReader v1.0.0

A focused PDF reading and productivity application designed for 
serious readers who want to track their progress, estimate study 
times, and take efficient notes.

🎯 Key Features:
• Smart time estimation based on your reading speed
• Pomodoro and Sprint timer modes
• Distraction-free focus modes
• Highlight-to-note functionality
• Local data storage (privacy-first)
• Comprehensive reading analytics

🛠️ Built with:
• Python & PyQt6 for the interface
• PyMuPDF for PDF handling
• PostgreSQL for local data storage
• Advanced analytics and prediction algorithms

© 2024 SprintReader Team. All rights reserved.
        """.strip()
        
        QMessageBox.about(self, "About SprintReader", about_text)
    
    # Window state management
    def restore_window_state(self):
        """Restore window state from settings"""
        try:
            # Restore window geometry
            geometry = self.settings.value('window_geometry')
            if geometry:
                self.restoreGeometry(geometry)
            
            # Restore last tab
            last_tab = self.settings.value('last_tab', 0, type=int)
            if 0 <= last_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(last_tab)
        
        except Exception as e:
            logger.error(f"Error restoring window state: {e}")
    
    def save_window_state(self):
        """Save window state to settings"""
        try:
            self.settings.setValue('window_geometry', self.saveGeometry())
            self.settings.setValue('last_tab', self.tab_widget.currentIndex())
        
        except Exception as e:
            logger.error(f"Error saving window state: {e}")
    
    # Utility methods
    def auto_save(self):
        """Perform automatic save operations"""
        try:
            # Save current reading progress
            if hasattr(self.pdf_viewer.pdf_handler, 'current_doc') and self.pdf_viewer.pdf_handler.current_doc:
                self.pdf_viewer.pdf_handler._save_progress()
            
            # Save window state
            self.save_window_state()
            
        except Exception as e:
            logger.error(f"Error during auto-save: {e}")
    
    def update_status(self):
        """Update status bar and UI elements"""
        try:
            # Update timer display
            if self.timer_manager.is_running():
                remaining_time = self.timer_manager.get_formatted_time()
                mode = self.timer_manager.get_current_mode().value.title()
                state = self.timer_manager.get_state().value.title()
                
                if state == "Break":
                    self.timer_display.setText(f"☕ Break: {remaining_time}")
                else:
                    self.timer_display.setText(f"⏱️ {mode}: {remaining_time}")
                
                # Update progress bar
                progress = self.timer_manager.get_progress_percentage()
                self.progress_bar.setValue(int(progress))
                self.progress_bar.setVisible(True)
                
                # Update session info
                self.session_info_label.setText(f"{mode} session active")
            else:
                self.timer_display.setText("⏱️ Ready")
                self.progress_bar.setVisible(False)
                self.session_info_label.setText("No active session")
            
            # Update other status elements
            if hasattr(self.pdf_viewer.pdf_handler, 'current_doc') and self.pdf_viewer.pdf_handler.current_doc:
                doc_info = self.pdf_viewer.pdf_handler.get_document_info()
                self.status_label.setText(
                    f"📖 {doc_info.get('title', 'Document')} - "
                    f"Page {doc_info.get('current_page', 1)}/{doc_info.get('total_pages', 0)} "
                    f"({doc_info.get('progress_percent', 0):.1f}%)"
                )
            elif not self.timer_manager.is_running() and not self.focus_mode_active:
                self.status_label.setText("Ready to start reading")
        
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    # Signal handlers
    def on_timer_started(self, mode):
        """Handle timer started signal"""
        self.notification_manager.send_notification(
            f"🎯 {mode.title()} Started",
            f"Focus session begun. Happy reading!"
        )
        self.update_timer_buttons()
    
    def on_timer_finished(self, mode):
        """Handle timer finished signal"""
        self.current_session_active = False
        self.notification_manager.send_timer_notification(mode, 'complete')
        self.update_timer_buttons()
        
        # Update dashboard
        self.dashboard.refresh_dashboard()
    
    def on_timer_paused(self):
        """Handle timer paused signal"""
        self.update_timer_buttons()
    
    def on_timer_resumed(self):
        """Handle timer resumed signal"""
        self.update_timer_buttons()
    
    def on_timer_updated(self, remaining_seconds):
        """Handle timer update signal"""
        # Status is updated in update_status method
        pass
    
    def on_document_opened(self, file_path):
        """Handle document opened signal"""
        self.quick_note_btn.setEnabled(True)
        
        # Update dashboard
        QTimer.singleShot(2000, self.dashboard.refresh_dashboard)
    
    def on_page_changed(self, page_number):
        """Handle page changed signal"""
        # This could trigger analytics updates
        pass
    
    def on_note_created(self, note_id):
        """Handle note created signal"""
        self.notification_manager.send_notification(
            "📝 Note Created",
            "New note added to your knowledge base!"
        )
    
    # Window events
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Save window state
            self.save_window_state()
            
            # Stop any active timers
            if self.timer_manager.is_running():
                self.timer_manager.stop()
            
            # Close PDF handler
            if hasattr(self.pdf_viewer.pdf_handler, 'current_doc') and self.pdf_viewer.pdf_handler.current_doc:
                self.pdf_viewer.pdf_handler.close_pdf()
            
            # Close analytics managers
            if self.analytics_manager:
                self.analytics_manager.close()
            
            if self.time_estimator:
                self.time_estimator.close()
            
            if self.reading_predictor:
                self.reading_predictor.close()
            
            logger.info("SprintReader closing gracefully")
            event.accept()
        
        except Exception as e:
            logger.error(f"Error during application close: {e}")
            event.accept()  # Close anyway


def main():
    """Main application entry point"""
    print("🚀 Starting SprintReader Final Version...")
    
    # Create logs directory in the correct location
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("SprintReader")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("SprintReader")
        app.setOrganizationDomain("sprintreader.app")
        
        # Initialize database
        print("🗄️ Initializing database...")
        try:
            db_manager.create_tables()
            initialize_stage5_settings()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to initialize database:\n{str(e)}\n\nPlease ensure PostgreSQL is running and configured correctly."
            )
            sys.exit(1)
        
        # Create and show main window
        print("🖥️ Creating main window...")
        window = SprintReaderMainWindow()
        window.show()
        
        print("✅ SprintReader started successfully!")
        print("")
        print("🎯 SprintReader Features:")
        print("  📖 Smart PDF reading with time estimation")
        print("  ⏱️ Pomodoro and Sprint timer modes")
        print("  🎯 Focus modes for distraction-free reading")
        print("  📝 Highlight-to-note functionality")
        print("  📊 Comprehensive reading analytics")
        print("  💾 Local-first data storage")
        print("")
        print("⌨️ Quick Start:")
        print("  • Ctrl+O to open a PDF")
        print("  • Ctrl+P for Pomodoro timer")
        print("  • Ctrl+S for Sprint timer")
        print("  • F11 for Focus Mode")
        print("  • Select text in PDF to create notes")
        print("")
        print("📚 Happy focused reading!")
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Critical error starting SprintReader: {e}")
        logger.critical(f"Critical startup error: {e}")
        
        # Show error dialog if possible
        try:
            if 'app' in locals():
                QMessageBox.critical(
                    None,
                    "SprintReader Error",
                    f"Failed to start SprintReader:\n{str(e)}\n\nCheck the logs for more details."
                )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()