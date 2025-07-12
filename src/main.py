"""
SprintReader Stage 5 Integration
Main file integrating Topic Management, Goal Setting, and Enhanced Focus Mode
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QTabWidget, QSplitter,
    QGroupBox, QTextEdit, QProgressBar, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QLineEdit, QDateEdit, QMessageBox,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QFont, QColor
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import Stage 5 components
from database.models import db_manager
from database.stage5_models import Stage5Manager, Topic, Goal, GoalType, FocusLevel
from stage5.topic_manager import TopicManager, TopicSummary
from stage5.goal_manager import GoalManager, GoalSummary, GoalType, GoalStatus
from stage5.enhanced_focus_manager import EnhancedFocusManager, FocusLevel

# Import existing components
from ui.pdf_viewer import PDFViewerWidget
from timer.timer_manager import TimerManager, TimerMode
from analytics.analytics_manager import AnalyticsManager
from notifications.notification_manager import NotificationManager

class TopicOverviewWidget(QWidget):
    """Widget showing topic overview with progress and goals"""
    
    topic_selected = pyqtSignal(int)  # topic_id
    focus_topic_requested = pyqtSignal(int)  # topic_id
    
    def __init__(self, topic_manager: TopicManager, goal_manager: GoalManager):
        super().__init__()
        self.topic_manager = topic_manager
        self.goal_manager = goal_manager
        self.current_topics = []
        
        self.init_ui()
        self.refresh_topics()
        
        # Connect signals
        self.topic_manager.topic_created.connect(self.refresh_topics)
        self.topic_manager.topic_updated.connect(self.refresh_topics)
        self.goal_manager.goal_updated.connect(self.refresh_topics)
    
    def init_ui(self):
        """Initialize the topic overview UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📚 Topic Overview")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add topic button
        self.add_topic_btn = QPushButton("➕ New Topic")
        self.add_topic_btn.clicked.connect(self.create_new_topic)
        header_layout.addWidget(self.add_topic_btn)
        
        layout.addLayout(header_layout)
        
        # Topics scroll area
        self.topics_scroll = QScrollArea()
        self.topics_scroll.setWidgetResizable(True)
        self.topics_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.topics_container = QWidget()
        self.topics_layout = QVBoxLayout(self.topics_container)
        self.topics_layout.addStretch()
        
        self.topics_scroll.setWidget(self.topics_container)
        layout.addWidget(self.topics_scroll)
    
    def refresh_topics(self):
        """Refresh topic display"""
        # Clear existing topics
        for i in reversed(range(self.topics_layout.count() - 1)):
            child = self.topics_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Get updated topic summaries
        self.current_topics = self.topic_manager.get_all_topic_summaries()
        
        # Add topic cards
        for topic_summary in self.current_topics:
            topic_card = self.create_topic_card(topic_summary)
            self.topics_layout.insertWidget(self.topics_layout.count() - 1, topic_card)
    
    def create_topic_card(self, topic_summary: TopicSummary) -> QWidget:
        """Create a topic card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {topic_summary.color};
                border-radius: 8px;
                margin: 4px;
                padding: 8px;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # Header with topic name and icon
        header_layout = QHBoxLayout()
        
        name_label = QLabel(f"{topic_summary.icon} {topic_summary.name}")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        name_label.setFont(font)
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Focus button
        focus_btn = QPushButton("🎯 Focus")
        focus_btn.clicked.connect(lambda: self.focus_topic_requested.emit(topic_summary.id))
        focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #7E22CE;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B21A8;
            }
        """)
        header_layout.addWidget(focus_btn)
        
        layout.addLayout(header_layout)
        
        # Description
        if topic_summary.description:
            desc_label = QLabel(topic_summary.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; margin: 4px 0;")
            layout.addWidget(desc_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(int(topic_summary.stats.completion_percentage))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{topic_summary.stats.completion_percentage:.1f}%")
        layout.addWidget(progress_bar)
        
        # Statistics grid
        stats_layout = QHBoxLayout()
        
        # Documents
        docs_label = QLabel(f"📄 {topic_summary.stats.total_documents} docs")
        docs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(docs_label)
        
        # Time
        time_label = QLabel(f"⏱️ {topic_summary.stats.time_spent:.0f}m")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(time_label)
        
        # Notes
        notes_label = QLabel(f"📝 {topic_summary.stats.notes_count} notes")
        notes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(notes_label)
        
        # Goals
        goals_label = QLabel(f"🎯 {topic_summary.stats.active_goals} goals")
        goals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(goals_label)
        
        layout.addLayout(stats_layout)
        
        # Estimated completion time
        if topic_summary.stats.estimated_time_remaining > 0:
            eta_label = QLabel(f"🏁 ~{topic_summary.stats.estimated_time_remaining:.0f} min remaining")
            eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            eta_label.setStyleSheet("color: #4169e1; font-weight: bold;")
            layout.addWidget(eta_label)
        
        # Make card clickable
        card.mousePressEvent = lambda event: self.topic_selected.emit(topic_summary.id)
        
        return card
    
    def create_new_topic(self):
        """Open dialog to create a new topic"""
        dialog = CreateTopicDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            topic_data = dialog.get_topic_data()
            self.topic_manager.create_topic(
                name=topic_data['name'],
                description=topic_data['description'],
                color=topic_data['color'],
                icon=topic_data['icon']
            )

class CreateTopicDialog(QDialog):
    """Dialog for creating new topics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Topic")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Topic name
        layout.addWidget(QLabel("Topic Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Machine Learning, History, Fiction")
        layout.addWidget(self.name_input)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Optional description of this topic...")
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)
        
        # Icon selection
        layout.addWidget(QLabel("Icon:"))
        self.icon_combo = QComboBox()
        icons = ["📚", "📖", "📝", "🎓", "🔬", "💼", "🏥", "⚖️", "🎨", "🏗️"]
        self.icon_combo.addItems(icons)
        layout.addWidget(self.icon_combo)
        
        # Color selection
        layout.addWidget(QLabel("Color:"))
        self.color_combo = QComboBox()
        colors = [
            ("#7E22CE", "Purple"), ("#DC2626", "Red"), ("#EA580C", "Orange"),
            ("#CA8A04", "Yellow"), ("#16A34A", "Green"), ("#2563EB", "Blue")
        ]
        for color_code, color_name in colors:
            self.color_combo.addItem(color_name, color_code)
        layout.addWidget(self.color_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Topic")
        create_btn.clicked.connect(self.accept)
        create_btn.setDefault(True)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def get_topic_data(self) -> dict:
        """Get topic data from dialog"""
        return {
            'name': self.name_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'icon': self.icon_combo.currentText(),
            'color': self.color_combo.currentData()
        }

class GoalsDashboardWidget(QWidget):
    """Widget showing goals dashboard with progress tracking"""
    
    def __init__(self, goal_manager: GoalManager, topic_manager: TopicManager):
        super().__init__()
        self.goal_manager = goal_manager
        self.topic_manager = topic_manager
        
        self.init_ui()
        self.refresh_goals()
        
        # Connect signals
        self.goal_manager.goal_created.connect(self.refresh_goals)
        self.goal_manager.goal_updated.connect(self.refresh_goals)
        self.goal_manager.goal_completed.connect(self.on_goal_completed)
    
    def init_ui(self):
        """Initialize goals dashboard UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎯 Goals Dashboard")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add goal button
        self.add_goal_btn = QPushButton("➕ New Goal")
        self.add_goal_btn.clicked.connect(self.create_new_goal)
        header_layout.addWidget(self.add_goal_btn)
        
        layout.addLayout(header_layout)
        
        # Daily progress summary
        self.daily_summary = QGroupBox("📅 Today's Progress")
        self.daily_summary_layout = QVBoxLayout(self.daily_summary)
        
        self.daily_progress_text = QTextEdit()
        self.daily_progress_text.setMaximumHeight(100)
        self.daily_progress_text.setReadOnly(True)
        self.daily_summary_layout.addWidget(self.daily_progress_text)
        
        layout.addWidget(self.daily_summary)
        
        # Active goals list
        self.goals_group = QGroupBox("🎯 Active Goals")
        self.goals_layout = QVBoxLayout(self.goals_group)
        
        self.goals_scroll = QScrollArea()
        self.goals_scroll.setWidgetResizable(True)
        
        self.goals_container = QWidget()
        self.goals_container_layout = QVBoxLayout(self.goals_container)
        self.goals_container_layout.addStretch()
        
        self.goals_scroll.setWidget(self.goals_container)
        self.goals_layout.addWidget(self.goals_scroll)
        
        layout.addWidget(self.goals_group)
    
    def refresh_goals(self):
        """Refresh goals display"""
        # Update daily summary
        self.update_daily_summary()
        
        # Clear existing goals
        for i in reversed(range(self.goals_container_layout.count() - 1)):
            child = self.goals_container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Get active goals
        active_goals = self.goal_manager.get_active_goals()
        
        # Add goal cards
        for goal_summary in active_goals:
            goal_card = self.create_goal_card(goal_summary)
            self.goals_container_layout.insertWidget(
                self.goals_container_layout.count() - 1, goal_card
            )
    
    def update_daily_summary(self):
        """Update daily progress summary"""
        dashboard_data = self.goal_manager.get_daily_goals_dashboard()
        
        summary_text = f"""
📊 Daily Goal Progress: {dashboard_data['daily_completion_percentage']:.1f}%

⏱️ Time Goals: {dashboard_data['current_progress']['time']:.0f} / {dashboard_data['total_daily_target']['time']:.0f} minutes
📄 Page Goals: {dashboard_data['current_progress']['pages']:.0f} / {dashboard_data['total_daily_target']['pages']:.0f} pages

✅ On Track: {dashboard_data['goals_on_track']} goals
⚠️ Behind: {dashboard_data['goals_behind']} goals
        """.strip()
        
        self.daily_progress_text.setText(summary_text)
    
    def create_goal_card(self, goal_summary: GoalSummary) -> QWidget:
        """Create a goal card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        
        # Status color coding
        status_colors = {
            GoalStatus.ON_TRACK: "#16A34A",
            GoalStatus.AHEAD: "#059669", 
            GoalStatus.BEHIND: "#EA580C",
            GoalStatus.AT_RISK: "#DC2626",
            GoalStatus.COMPLETED: "#7C3AED"
        }
        
        status_color = status_colors.get(goal_summary.progress.status, "#6B7280")
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {status_color};
                border-radius: 8px;
                margin: 4px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # Goal header
        header_layout = QHBoxLayout()
        
        # Goal type icon and target
        goal_type_icons = {
            GoalType.TIME_BASED: "⏱️",
            GoalType.PAGE_BASED: "📄", 
            GoalType.DEADLINE_BASED: "📅"
        }
        
        icon = goal_type_icons.get(goal_summary.goal_type, "🎯")
        goal_text = f"{icon} {goal_summary.target_value:.0f} {goal_summary.goal_type.value}"
        
        goal_label = QLabel(goal_text)
        font = QFont()
        font.setBold(True)
        goal_label.setFont(font)
        header_layout.addWidget(goal_label)
        
        header_layout.addStretch()
        
        # Status badge
        status_badge = QLabel(goal_summary.progress.status.value.replace('_', ' ').title())
        status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {status_color};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(status_badge)
        
        layout.addLayout(header_layout)
        
        # Target context (topic or document)
        if goal_summary.topic_name:
            context_label = QLabel(f"📚 Topic: {goal_summary.topic_name}")
        elif goal_summary.document_title:
            context_label = QLabel(f"📄 Document: {goal_summary.document_title}")
        else:
            context_label = QLabel("🌐 General Goal")
        
        context_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(context_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(int(goal_summary.progress.progress_percentage))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{goal_summary.current_value:.0f} / {goal_summary.target_value:.0f}")
        layout.addWidget(progress_bar)
        
        # Goal details
        details_layout = QHBoxLayout()
        
        # Progress percentage
        progress_label = QLabel(f"📊 {goal_summary.progress.progress_percentage:.1f}%")
        details_layout.addWidget(progress_label)
        
        # Days remaining
        if goal_summary.progress.days_remaining > 0:
            days_label = QLabel(f"📅 {goal_summary.progress.days_remaining} days left")
            details_layout.addWidget(days_label)
        
        # Daily target
        if goal_summary.progress.daily_target > 0:
            daily_label = QLabel(f"📈 {goal_summary.progress.daily_target:.1f}/day")
            details_layout.addWidget(daily_label)
        
        layout.addLayout(details_layout)
        
        # Adaptive suggestion
        if goal_summary.progress.adaptive_suggestion:
            suggestion_label = QLabel(f"💡 {goal_summary.progress.adaptive_suggestion}")
            suggestion_label.setWordWrap(True)
            suggestion_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8ff;
                    border: 1px solid #4169e1;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 11px;
                }
            """)
            layout.addWidget(suggestion_label)
        
        return card
    
    def create_new_goal(self):
        """Open dialog to create a new goal"""
        dialog = CreateGoalDialog(self.topic_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            self.goal_manager.create_goal(
                goal_type=goal_data['goal_type'],
                target_value=goal_data['target_value'],
                target_date=goal_data['target_date'],
                topic_id=goal_data['topic_id'],
                document_id=goal_data['document_id']
            )
    
    def on_goal_completed(self, goal_id: int, description: str):
        """Handle goal completion"""
        QMessageBox.information(
            self,
            "🎉 Goal Completed!",
            f"Congratulations! You've completed:\n{description}"
        )

class CreateGoalDialog(QDialog):
    """Dialog for creating new goals"""
    
    def __init__(self, topic_manager: TopicManager, parent=None):
        super().__init__(parent)
        self.topic_manager = topic_manager
        self.setWindowTitle("Create New Goal")
        self.setModal(True)
        self.resize(400, 350)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Goal type
        layout.addWidget(QLabel("Goal Type:"))
        self.goal_type_combo = QComboBox()
        self.goal_type_combo.addItem("⏱️ Time-Based (minutes)", GoalType.TIME_BASED)
        self.goal_type_combo.addItem("📄 Page-Based", GoalType.PAGE_BASED)
        self.goal_type_combo.addItem("📅 Deadline-Based", GoalType.DEADLINE_BASED)
        self.goal_type_combo.currentTextChanged.connect(self.on_goal_type_changed)
        layout.addWidget(self.goal_type_combo)
        
        # Target value
        layout.addWidget(QLabel("Target Value:"))
        target_layout = QHBoxLayout()
        self.target_spinbox = QSpinBox()
        self.target_spinbox.setRange(1, 10000)
        self.target_spinbox.setValue(100)
        target_layout.addWidget(self.target_spinbox)
        
        self.target_unit_label = QLabel("pages")
        target_layout.addWidget(self.target_unit_label)
        target_layout.addStretch()
        layout.addLayout(target_layout)
        
        # Target date (for deadline goals)
        layout.addWidget(QLabel("Target Date:"))
        self.target_date = QDateEdit()
        self.target_date.setDate(QDate.currentDate().addDays(7))
        self.target_date.setCalendarPopup(True)
        self.target_date.setEnabled(False)
        layout.addWidget(self.target_date)
        
        # Scope selection
        layout.addWidget(QLabel("Goal Scope:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("🌐 General Goal", "general")
        
        # Add topics
        topics = self.topic_manager.get_all_topics()
        for topic in topics:
            self.scope_combo.addItem(f"📚 Topic: {topic.name}", f"topic_{topic.id}")
        
        layout.addWidget(self.scope_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Goal")
        create_btn.clicked.connect(self.accept)
        create_btn.setDefault(True)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def on_goal_type_changed(self):
        """Handle goal type change"""
        goal_type = self.goal_type_combo.currentData()
        
        if goal_type == GoalType.TIME_BASED:
            self.target_unit_label.setText("minutes")
            self.target_spinbox.setValue(150)  # 2.5 hours default
            self.target_date.setEnabled(False)
        elif goal_type == GoalType.PAGE_BASED:
            self.target_unit_label.setText("pages")
            self.target_spinbox.setValue(100)
            self.target_date.setEnabled(False)
        elif goal_type == GoalType.DEADLINE_BASED:
            self.target_unit_label.setText("by deadline")
            self.target_date.setEnabled(True)
    
    def get_goal_data(self) -> dict:
        """Get goal data from dialog"""
        scope_data = self.scope_combo.currentData()
        topic_id = None
        document_id = None
        
        if scope_data.startswith("topic_"):
            topic_id = int(scope_data.split("_")[1])
        
        target_date = None
        if self.target_date.isEnabled():
            target_date = self.target_date.date().toPython()
            target_date = datetime.combine(target_date, datetime.min.time())
        
        return {
            'goal_type': self.goal_type_combo.currentData(),
            'target_value': self.target_spinbox.value(),
            'target_date': target_date,
            'topic_id': topic_id,
            'document_id': document_id
        }

class Stage5MainWindow(QMainWindow):
    """Enhanced main window with Stage 5 features"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.stage5_manager = Stage5Manager(db_manager)
        self.topic_manager = TopicManager()
        self.goal_manager = GoalManager()
        self.enhanced_focus_manager = EnhancedFocusManager()
        
        # Existing managers
        self.timer_manager = TimerManager()
        self.analytics_manager = AnalyticsManager()
        self.notification_manager = NotificationManager()
        
        # Current state
        self.current_topic_id = None
        self.focus_session_active = False
        
        self.init_ui()
        self.init_database()
        self.init_menu_bar()
        self.connect_signals()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the enhanced UI"""
        self.setWindowTitle("SprintReader Stage 5 - Topic-Based Goal Setting & Focus Mode")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Enhanced toolbar
        self.create_enhanced_toolbar(main_layout)
        
        # Main content area with tabs
        self.content_tabs = QTabWidget()
        
        # Tab 1: Topic Overview
        self.topic_overview = TopicOverviewWidget(self.topic_manager, self.goal_manager)
        self.content_tabs.addTab(self.topic_overview, "📚 Topics")
        
        # Tab 2: Goals Dashboard
        self.goals_dashboard = GoalsDashboardWidget(self.goal_manager, self.topic_manager)
        self.content_tabs.addTab(self.goals_dashboard, "🎯 Goals")
        
        # Tab 3: PDF Reader (enhanced)
        self.pdf_viewer = PDFViewerWidget()
        self.content_tabs.addTab(self.pdf_viewer, "📖 Reader")
        
        # Tab 4: Focus Analytics
        self.create_focus_analytics_tab()
        self.content_tabs.addTab(self.focus_analytics_widget, "📊 Focus Analytics")
        
        main_layout.addWidget(self.content_tabs)
        
        # Enhanced status bar
        self.create_enhanced_status_bar(main_layout)
    
    def create_enhanced_toolbar(self, parent_layout):
        """Create enhanced toolbar with Stage 5 features"""
        toolbar_layout = QHBoxLayout()
        
        # Focus mode controls
        focus_group = QGroupBox("🎯 Focus Mode")
        focus_layout = QHBoxLayout(focus_group)
        
        # Focus level selection
        self.focus_level_combo = QComboBox()
        self.focus_level_combo.addItem("Minimal", FocusLevel.MINIMAL)
        self.focus_level_combo.addItem("Standard", FocusLevel.STANDARD)
        self.focus_level_combo.addItem("Deep", FocusLevel.DEEP)
        self.focus_level_combo.addItem("Immersive", FocusLevel.IMMERSIVE)
        self.focus_level_combo.setCurrentIndex(1)  # Standard default
        focus_layout.addWidget(self.focus_level_combo)
        
        # Focus session button
        self.focus_session_btn = QPushButton("🎯 Start Focus Session")
        self.focus_session_btn.clicked.connect(self.toggle_focus_session)
        self.focus_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #7E22CE;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B21A8;
            }
        """)
        focus_layout.addWidget(self.focus_session_btn)
        
        toolbar_layout.addWidget(focus_group)
        
        # Current topic selector
        topic_group = QGroupBox("📚 Current Topic")
        topic_layout = QHBoxLayout(topic_group)
        
        self.current_topic_combo = QComboBox()
        self.current_topic_combo.addItem("No Topic Selected", None)
        self.update_topic_selector()
        topic_layout.addWidget(self.current_topic_combo)
        
        toolbar_layout.addWidget(topic_group)
        
        # Quick actions
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        quick_goal_btn = QPushButton("🎯 Quick Goal")
        quick_goal_btn.clicked.connect(self.create_quick_goal)
        actions_layout.addWidget(quick_goal_btn)
        
        topic_progress_btn = QPushButton("📊 Topic Progress")
        topic_progress_btn.clicked.connect(self.show_topic_progress)
        actions_layout.addWidget(topic_progress_btn)
        
        toolbar_layout.addWidget(actions_group)
        
        toolbar_layout.addStretch()
        
        # Focus session info
        self.focus_session_info = QLabel("🎯 Ready for Focus")
        self.focus_session_info.setStyleSheet("font-weight: bold; color: #7E22CE;")
        toolbar_layout.addWidget(self.focus_session_info)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_focus_analytics_tab(self):
        """Create focus analytics tab"""
        self.focus_analytics_widget = QWidget()
        layout = QVBoxLayout(self.focus_analytics_widget)
        
        # Analytics header
        header_label = QLabel("📊 Focus & Productivity Analytics")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        header_label.setFont(font)
        layout.addWidget(header_label)
        
        # Analytics content
        self.focus_analytics_text = QTextEdit()
        self.focus_analytics_text.setReadOnly(True)
        layout.addWidget(self.focus_analytics_text)
        
        # Refresh analytics
        refresh_btn = QPushButton("🔄 Refresh Analytics")
        refresh_btn.clicked.connect(self.update_focus_analytics)
        layout.addWidget(refresh_btn)
        
        # Initial load
        self.update_focus_analytics()
    
    def create_enhanced_status_bar(self, parent_layout):
        """Create enhanced status bar"""
        status_layout = QHBoxLayout()
        
        # Current session info
        self.session_status = QLabel("📚 Ready")
        status_layout.addWidget(self.session_status)
        
        status_layout.addWidget(QLabel(" | "))
        
        # Daily progress
        self.daily_progress_label = QLabel("📅 Daily: 0%")
        status_layout.addWidget(self.daily_progress_label)
        
        status_layout.addWidget(QLabel(" | "))
        
        # Active goals
        self.active_goals_label = QLabel("🎯 Goals: 0 active")
        status_layout.addWidget(self.active_goals_label)
        
        status_layout.addStretch()
        
        # Focus productivity score
        self.productivity_score_label = QLabel("⚡ Productivity: --")
        status_layout.addWidget(self.productivity_score_label)
        
        parent_layout.addLayout(status_layout)
        
        # Start status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def init_database(self):
        """Initialize database with Stage 5 tables"""
        try:
            self.stage5_manager.create_stage5_tables()
            print("✅ Stage 5 Database initialized")
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to initialize Stage 5 database:\n{str(e)}"
            )
    
    def init_menu_bar(self):
        """Initialize enhanced menu bar"""
        menubar = self.menuBar()
        
        # File Menu (enhanced)
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open PDF...', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.pdf_viewer.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_topic_action = QAction('Export &Topic Summary...', self)
        export_topic_action.triggered.connect(self.export_current_topic)
        file_menu.addAction(export_topic_action)
        
        # Focus Menu (new)
        focus_menu = menubar.addMenu('&Focus')
        
        start_focus_action = QAction('&Start Focus Session', self)
        start_focus_action.setShortcut(QKeySequence('F11'))
        start_focus_action.triggered.connect(self.toggle_focus_session)
        focus_menu.addAction(start_focus_action)
        
        focus_topic_action = QAction('Focus on Current &Topic', self)
        focus_topic_action.setShortcut(QKeySequence('Ctrl+Shift+F'))
        focus_topic_action.triggered.connect(self.focus_on_current_topic)
        focus_menu.addAction(focus_topic_action)
        
        # Goals Menu (new)
        goals_menu = menubar.addMenu('&Goals')
        
        quick_goal_action = QAction('&Quick Goal...', self)
        quick_goal_action.setShortcut(QKeySequence('Ctrl+G'))
        quick_goal_action.triggered.connect(self.create_quick_goal)
        goals_menu.addAction(quick_goal_action)
        
        goals_progress_action = QAction('&Goals Progress', self)
        goals_progress_action.triggered.connect(self.show_goals_progress)
        goals_menu.addAction(goals_progress_action)
    
    def connect_signals(self):
        """Connect all Stage 5 signals"""
        # Topic signals
        self.topic_overview.topic_selected.connect(self.on_topic_selected)
        self.topic_overview.focus_topic_requested.connect(self.focus_on_topic)
        
        # Focus manager signals
        self.enhanced_focus_manager.focus_session_started.connect(self.on_focus_session_started)
        self.enhanced_focus_manager.focus_session_ended.connect(self.on_focus_session_ended)
        self.enhanced_focus_manager.productivity_alert.connect(self.on_productivity_alert)
        
        # Goal manager signals
        self.goal_manager.goal_completed.connect(self.on_goal_completed)
        self.goal_manager.goal_at_risk.connect(self.on_goal_at_risk)
    
    def toggle_focus_session(self):
        """Toggle focus session on/off"""
        if self.focus_session_active:
            self.end_focus_session()
        else:
            self.start_focus_session()
    
    def start_focus_session(self):
        """Start a focus session"""
        focus_level = self.focus_level_combo.currentData()
        current_topic_id = self.current_topic_combo.currentData()
        
        # Apply focus level to UI
        self.enhanced_focus_manager.apply_focus_level(self, focus_level)
        
        # Start session tracking
        session_id = self.enhanced_focus_manager.start_focus_session(
            topic_id=current_topic_id
        )
        
        self.focus_session_active = True
        self.focus_session_btn.setText("⏹️ End Focus Session")
        
        # Switch to PDF reader tab during focus
        self.content_tabs.setCurrentIndex(2)  # PDF Reader tab
        
        print(f"🎯 Focus session started with {focus_level.value} level")
    
    def end_focus_session(self):
        """End current focus session"""
        # Remove focus mode
        self.enhanced_focus_manager.remove_focus_mode(self)
        
        # End session tracking
        session_summary = self.enhanced_focus_manager.end_focus_session()
        
        self.focus_session_active = False
        self.focus_session_btn.setText("🎯 Start Focus Session")
        
        # Show session summary
        if session_summary:
            self.show_focus_session_summary(session_summary)
        
        print("📊 Focus session ended")
    
    def show_focus_session_summary(self, session_summary: dict):
        """Show focus session summary dialog"""
        summary_text = f"""
🎯 Focus Session Complete!

⏱️ Duration: {session_summary['duration']:.1f} minutes
📄 Pages Read: {session_summary['pages_read']}
⚡ Productivity Score: {session_summary['productivity_score']:.1f}/100
🚫 Interruptions: {session_summary['interruptions']}
🎯 Focus Level: {session_summary['focus_level'].title()}
📈 Reading Speed: {session_summary['average_reading_speed']:.1f}s/page
        """.strip()
        
        QMessageBox.information(self, "Session Complete", summary_text)
    
    def update_topic_selector(self):
        """Update the current topic selector"""
        current_selection = self.current_topic_combo.currentData()
        self.current_topic_combo.clear()
        self.current_topic_combo.addItem("No Topic Selected", None)
        
        topics = self.topic_manager.get_all_topics()
        for topic in topics:
            self.current_topic_combo.addItem(f"{topic.icon or '📚'} {topic.name}", topic.id)
        
        # Restore selection if possible
        if current_selection:
            for i in range(self.current_topic_combo.count()):
                if self.current_topic_combo.itemData(i) == current_selection:
                    self.current_topic_combo.setCurrentIndex(i)
                    break
    
    def update_status_bar(self):
        """Update status bar information"""
        # Update daily progress
        dashboard_data = self.goal_manager.get_daily_goals_dashboard()
        self.daily_progress_label.setText(
            f"📅 Daily: {dashboard_data['daily_completion_percentage']:.0f}%"
        )
        
        # Update active goals
        active_goals_count = dashboard_data['total_active_goals']
        self.active_goals_label.setText(f"🎯 Goals: {active_goals_count} active")
        
        # Update productivity score if in focus session
        if self.focus_session_active:
            session_info = self.enhanced_focus_manager.get_current_session_info()
            if session_info:
                score = session_info['productivity_score']
                self.productivity_score_label.setText(f"⚡ Productivity: {score:.0f}/100")
                
                # Update focus session info
                duration = session_info['duration']
                pages = session_info['pages_read']
                self.focus_session_info.setText(
                    f"🎯 Focus: {duration:.0f}m, {pages} pages, {score:.0f}% productive"
                )
        else:
            self.productivity_score_label.setText("⚡ Productivity: --")
            self.focus_session_info.setText("🎯 Ready for Focus")
    
    def update_focus_analytics(self):
        """Update focus analytics display"""
        analytics = self.enhanced_focus_manager.get_focus_analytics(30)  # Last 30 days
        recommendations = self.enhanced_focus_manager.get_focus_recommendations()
        
        analytics_text = f"""
# 📊 Focus & Productivity Analytics (Last 30 Days)

## 🎯 Session Overview
- **Total Sessions:** {analytics.total_sessions}
- **Total Focus Time:** {analytics.total_focus_time:.1f} minutes
- **Average Session:** {analytics.average_session_length:.1f} minutes
- **Average Productivity:** {analytics.average_productivity_score:.1f}/100

## ⏰ Timing Insights
- **Most Productive Time:** {analytics.most_productive_time}
- **Consistency Score:** {analytics.consistency_score:.1f}%
- **Interruption Rate:** {analytics.interruption_rate:.2f} per minute

## 💡 Personalized Recommendations
"""
        
        for i, rec in enumerate(recommendations, 1):
            analytics_text += f"{i}. {rec}\n"
        
        if analytics.total_sessions == 0:
            analytics_text += "\n📝 **No focus sessions yet!** Start your first session to see analytics."
        
        self.focus_analytics_text.setPlainText(analytics_text)
    
    def refresh_all_data(self):
        """Refresh all data displays"""
        self.topic_overview.refresh_topics()
        self.goals_dashboard.refresh_goals()
        self.update_topic_selector()
        self.update_focus_analytics()
    
    def on_topic_selected(self, topic_id: int):
        """Handle topic selection"""
        self.current_topic_id = topic_id
        
        # Set in topic selector
        for i in range(self.current_topic_combo.count()):
            if self.current_topic_combo.itemData(i) == topic_id:
                self.current_topic_combo.setCurrentIndex(i)
                break
        
        # Show topic details
        topic = self.topic_manager.get_topic_by_id(topic_id)
        if topic:
            self.session_status.setText(f"📚 Topic: {topic.name}")
    
    def focus_on_topic(self, topic_id: int):
        """Start focus session for specific topic"""
        # Select the topic
        self.on_topic_selected(topic_id)
        
        # Start focus session
        self.start_focus_session()
    
    def focus_on_current_topic(self):
        """Focus on currently selected topic"""
        current_topic_id = self.current_topic_combo.currentData()
        if current_topic_id:
            self.focus_on_topic(current_topic_id)
        else:
            QMessageBox.information(
                self, 
                "No Topic Selected", 
                "Please select a topic first to start a focused session."
            )
    
    def create_quick_goal(self):
        """Create a quick goal dialog"""
        dialog = CreateGoalDialog(self.topic_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            goal_id = self.goal_manager.create_goal(
                goal_type=goal_data['goal_type'],
                target_value=goal_data['target_value'],
                target_date=goal_data['target_date'],
                topic_id=goal_data['topic_id'],
                document_id=goal_data['document_id']
            )
            
            if goal_id:
                QMessageBox.information(
                    self,
                    "Goal Created",
                    f"Successfully created {goal_data['goal_type'].value} goal!"
                )
    
    def show_topic_progress(self):
        """Show detailed topic progress"""
        current_topic_id = self.current_topic_combo.currentData()
        if not current_topic_id:
            QMessageBox.information(
                self,
                "No Topic Selected",
                "Please select a topic to view progress."
            )
            return
        
        topic_summary = self.topic_manager.get_topic_summary(current_topic_id)
        if topic_summary:
            progress_text = self.topic_manager.export_topic_summary(current_topic_id)
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Progress: {topic_summary.name}")
            dialog.resize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_display = QTextEdit()
            text_display.setPlainText(progress_text)
            text_display.setReadOnly(True)
            layout.addWidget(text_display)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
    
    def show_goals_progress(self):
        """Show goals progress overview"""
        weekly_overview = self.goal_manager.get_weekly_goals_overview()
        
        progress_text = f"""
# 🎯 Goals Progress Overview

## 📊 This Week's Summary
- **Goals Completed:** {weekly_overview['goals_completed_this_week']}
- **Goals On Track:** {weekly_overview['goals_on_track']}
- **Goals Behind:** {weekly_overview['goals_behind']}

## ⏱️ Time Goals
- **Target:** {weekly_overview['total_time_target']:.0f} minutes
- **Achieved:** {weekly_overview['total_time_achieved']:.0f} minutes
- **Progress:** {(weekly_overview['total_time_achieved']/weekly_overview['total_time_target']*100) if weekly_overview['total_time_target'] > 0 else 0:.1f}%

## 📄 Page Goals
- **Target:** {weekly_overview['total_pages_target']:.0f} pages
- **Achieved:** {weekly_overview['total_pages_achieved']:.0f} pages
- **Progress:** {(weekly_overview['total_pages_achieved']/weekly_overview['total_pages_target']*100) if weekly_overview['total_pages_target'] > 0 else 0:.1f}%
        """
        
        if weekly_overview['most_progress_goal']:
            goal = weekly_overview['most_progress_goal']
            progress_text += f"\n## 🏆 Top Performer\n**{goal.goal_type.value.title()} Goal:** {goal.progress.progress_percentage:.1f}% complete"
        
        QMessageBox.information(self, "Goals Progress", progress_text)
    
    def export_current_topic(self):
        """Export current topic summary"""
        current_topic_id = self.current_topic_combo.currentData()
        if not current_topic_id:
            QMessageBox.information(
                self,
                "No Topic Selected",
                "Please select a topic to export."
            )
            return
        
        from PyQt6.QtWidgets import QFileDialog
        
        topic = self.topic_manager.get_topic_by_id(current_topic_id)
        if not topic:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Topic Summary",
            f"{topic.name}_summary.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                summary_text = self.topic_manager.export_topic_summary(current_topic_id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(summary_text)
                
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Topic summary exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export topic summary:\n{str(e)}"
                )
    
    def on_focus_session_started(self, session_id: int, focus_level: str):
        """Handle focus session start"""
        self.notification_manager.send_notification(
            f"🎯 Focus Session Started",
            f"Entering {focus_level} focus mode. Happy reading!"
        )
    
    def on_focus_session_ended(self, session_id: int, session_data: dict):
        """Handle focus session end"""
        duration = session_data.get('duration', 0)
        productivity = session_data.get('productivity_score', 0)
        
        self.notification_manager.send_notification(
            "📊 Focus Session Complete",
            f"Completed {duration:.0f}min session with {productivity:.0f}% productivity!"
        )
    
    def on_productivity_alert(self, alert_type: str, message: str):
        """Handle productivity alerts"""
        if alert_type == "distraction":
            QMessageBox.warning(self, "Focus Alert", message)
        else:
            self.notification_manager.send_notification("⚡ Productivity Alert", message)
    
    def on_goal_completed(self, goal_id: int, description: str):
        """Handle goal completion"""
        self.notification_manager.send_notification(
            "🎉 Goal Completed!",
            f"Congratulations! {description}"
        )
        
        # Update related goals progress for same topic
        goal = self.goal_manager.get_goal_by_id(goal_id)
        if goal and goal.topic_id:
            # Refresh topic display
            self.topic_overview.refresh_topics()
    
    def on_goal_at_risk(self, goal_id: int, warning_message: str):
        """Handle goal at risk warning"""
        self.notification_manager.send_notification(
            "⚠️ Goal At Risk",
            warning_message
        )
    
    def closeEvent(self, event):
        """Handle application close"""
        # End any active focus session
        if self.focus_session_active:
            self.end_focus_session()
        
        # Save any pending data
        try:
            # Close database connections
            if hasattr(self, 'analytics_manager'):
                self.analytics_manager.close()
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
        
        event.accept()

def main():
    """Main application entry point for Stage 5"""
    print("🚀 Starting SprintReader Stage 5...")
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("SprintReader Stage 5")
        app.setApplicationVersion("5.0.0")
        app.setOrganizationName("SprintReader")
        app.setStyle('Fusion')
        
        # Create main window
        window = Stage5MainWindow()
        window.show()
        
        print("✅ SprintReader Stage 5 launched successfully!")
        print("📚 New Features:")
        print("  • Topic-based PDF organization")
        print("  • Adaptive goal setting with progress tracking")
        print("  • Enhanced focus mode with productivity analytics")
        print("  • Smart time estimation and recommendations")
        print("  • Multi-level focus modes (Minimal → Immersive)")
        print("🎯 Use F11 to start focus sessions")
        print("📊 Check Focus Analytics tab for productivity insights")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error starting SprintReader Stage 5: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()