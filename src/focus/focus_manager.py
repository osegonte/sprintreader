"""
Focus Manager - Enhanced with Stage 5 Productivity Analytics
Controls distraction-free reading mode with advanced tracking
"""

from qt_compat import QObject, QTimer, pyqtSignal, QSettings, QWidget
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

class FocusLevel(Enum):
    """Stage 5: Enhanced focus levels"""
    MINIMAL = "minimal"      # Hide sidebar only
    STANDARD = "standard"    # Hide sidebar + toolbar  
    DEEP = "deep"           # Hide everything except PDF
    IMMERSIVE = "immersive" # Full-screen + ambient features

class FocusManager(QObject):
    """Enhanced focus manager with Stage 5 productivity tracking"""
    
    # Existing signals
    focus_mode_enabled = pyqtSignal()
    focus_mode_disabled = pyqtSignal()
    settings_changed = pyqtSignal(dict)
    
    # Stage 5: New signals
    focus_session_started = pyqtSignal(str, str)  # session_id, focus_level
    focus_session_ended = pyqtSignal(str, dict)   # session_id, session_data
    productivity_alert = pyqtSignal(str, str)     # alert_type, message
    break_recommendation = pyqtSignal(int)        # recommended_break_minutes
    
    def __init__(self):
        super().__init__()
        self.is_focus_mode = False
        self.settings = QSettings('SprintReader', 'Focus')
        
        # Stage 5: Enhanced focus state
        self.current_focus_level = FocusLevel.STANDARD
        self.current_session = None
        self.session_start_time = None
        self.pages_read_in_session = 0
        self.interruption_count = 0
        self.last_activity_time = datetime.now()
        self.page_read_times = []
        
        # Default focus settings (enhanced for Stage 5)
        self.focus_settings = {
            'hide_sidebar': True,
            'hide_toolbar': False,
            'hide_statusbar': True,
            'dim_background': True,
            'show_timer_overlay': True,
            'auto_hide_cursor': True,
            'minimal_notifications': True,
            'ambient_sounds': False,
            # Stage 5: New settings
            'default_focus_level': 'standard',
            'productivity_tracking': True,
            'auto_break_reminders': True,
            'break_interval_minutes': 25,
            'idle_detection': True,
            'session_analytics': True
        }
        
        self._load_settings()
        
        # Track hidden widgets for restoration
        self.hidden_widgets = []
        self.original_states = {}
        
        # Stage 5: Productivity timers
        self.productivity_timer = QTimer()
        self.productivity_timer.timeout.connect(self._check_productivity_metrics)
        
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._check_idle_state)
        self.idle_timer.start(30000)  # Check every 30 seconds
        
        self.break_reminder_timer = QTimer()
        self.break_reminder_timer.timeout.connect(self._suggest_break)
    
    # Stage 5: Enhanced focus session management
    def start_focus_session(self, topic_id: int = None, document_id: int = None, 
                          focus_level: FocusLevel = None) -> str:
        """Start enhanced focus session with tracking"""
        if self.current_session:
            self.end_focus_session()
        
        if focus_level is None:
            focus_level = FocusLevel(self.focus_settings['default_focus_level'])
        
        # Initialize session tracking
        session_id = f"focus_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = {
            'id': session_id,
            'topic_id': topic_id,
            'document_id': document_id,
            'focus_level': focus_level,
            'start_time': datetime.now(),
            'pages_read': 0,
            'interruptions': 0
        }
        
        self.session_start_time = datetime.now()
        self.pages_read_in_session = 0
        self.interruption_count = 0
        self.page_read_times = []
        self.last_activity_time = datetime.now()
        
        # Start productivity tracking
        if self.focus_settings.get('productivity_tracking', True):
            self.productivity_timer.start(60000)  # Check every minute
        
        # Set break reminders
        if self.focus_settings.get('auto_break_reminders', True):
            break_interval = self.focus_settings.get('break_interval_minutes', 25) * 60000
            self.break_reminder_timer.start(break_interval)
        
        self.focus_session_started.emit(session_id, focus_level.value)
        print(f"🎯 Enhanced focus session started: {focus_level.value}")
        
        return session_id
    
    def end_focus_session(self) -> Optional[Dict]:
        """End focus session and return analytics"""
        if not self.current_session:
            return None
        
        # Calculate session metrics
        end_time = datetime.now()
        duration = (end_time - self.session_start_time).total_seconds() / 60  # minutes
        
        # Calculate productivity score
        productivity_score = self._calculate_productivity_score()
        
        # Prepare session summary
        session_summary = {
            'session_id': self.current_session['id'],
            'duration': duration,
            'pages_read': self.pages_read_in_session,
            'productivity_score': productivity_score,
            'interruptions': self.interruption_count,
            'focus_level': self.current_session['focus_level'].value,
            'average_reading_speed': self._calculate_average_reading_speed(),
            'topic_id': self.current_session.get('topic_id'),
            'document_id': self.current_session.get('document_id')
        }
        
        # Save session to database
        self._save_focus_session_to_db(session_summary)
        
        # Stop timers
        self.productivity_timer.stop()
        self.break_reminder_timer.stop()
        
        # Reset session state
        session_id = self.current_session['id']
        self.current_session = None
        self.session_start_time = None
        
        self.focus_session_ended.emit(session_id, session_summary)
        print(f"📊 Focus session ended: {duration:.1f}min, {productivity_score:.1f}% productive")
        
        return session_summary
    
    def apply_focus_level(self, main_window, focus_level: FocusLevel):
        """Apply specific focus level to the interface"""
        self.current_focus_level = focus_level
        
        # Store original window state if not already stored
        if not hasattr(self, 'original_window_state') or not self.original_window_state:
            self.original_window_state = {
                'geometry': main_window.geometry(),
                'window_state': main_window.windowState()
            }
        
        # Clear previous hidden widgets
        self._restore_hidden_widgets()
        
        # Apply focus level
        if focus_level == FocusLevel.MINIMAL:
            self._apply_minimal_focus(main_window)
        elif focus_level == FocusLevel.STANDARD:
            self._apply_standard_focus(main_window)
        elif focus_level == FocusLevel.DEEP:
            self._apply_deep_focus(main_window)
        elif focus_level == FocusLevel.IMMERSIVE:
            self._apply_immersive_focus(main_window)
        
        print(f"🎯 Applied {focus_level.value} focus level")
    
    # Existing enable/disable methods enhanced
    def enable_focus_mode(self, main_window, focus_level: FocusLevel = None):
        """Enable focus mode with specified level"""
        if self.is_focus_mode:
            return
        
        if focus_level is None:
            focus_level = FocusLevel(self.focus_settings.get('default_focus_level', 'standard'))
        
        self.apply_focus_level(main_window, focus_level)
        self.is_focus_mode = True
        self.focus_mode_enabled.emit()
    
    def disable_focus_mode(self, main_window):
        """Disable focus mode and restore normal interface"""
        if not self.is_focus_mode:
            return
        
        self.is_focus_mode = False
        
        # Restore all hidden widgets
        self._restore_hidden_widgets()
        
        # Restore original window state
        if hasattr(self, 'original_window_state') and self.original_window_state:
            main_window.setGeometry(self.original_window_state['geometry'])
            main_window.setWindowState(self.original_window_state['window_state'])
        
        # Remove focus styling
        main_window.setStyleSheet("")
        
        self.focus_mode_disabled.emit()
        print("🔍 Focus mode disabled")
    
    def toggle_focus_mode(self, main_window, focus_level: FocusLevel = None):
        """Toggle focus mode on/off"""
        if self.is_focus_mode:
            self.disable_focus_mode(main_window)
        else:
            self.enable_focus_mode(main_window, focus_level)
    
    # Stage 5: New focus level implementations
    def _apply_minimal_focus(self, main_window):
        """Apply minimal focus: hide sidebar only"""
        sidebar = getattr(main_window, 'sidebar', None)
        if sidebar:
            self._hide_widget(sidebar)
    
    def _apply_standard_focus(self, main_window):
        """Apply standard focus: hide sidebar and non-essential elements"""
        # Hide sidebar
        sidebar = getattr(main_window, 'sidebar', None)
        if sidebar:
            self._hide_widget(sidebar)
        
        # Hide status bar if setting enabled
        if self.focus_settings.get('hide_statusbar', True):
            statusbar = main_window.statusBar()
            if statusbar:
                self._hide_widget(statusbar)
    
    def _apply_deep_focus(self, main_window):
        """Apply deep focus: hide everything except PDF and minimal controls"""
        # Hide sidebar
        sidebar = getattr(main_window, 'sidebar', None)
        if sidebar:
            self._hide_widget(sidebar)
        
        # Hide status bar
        statusbar = main_window.statusBar()
        if statusbar:
            self._hide_widget(statusbar)
        
        # Hide menu bar
        menubar = main_window.menuBar()
        if menubar:
            self._hide_widget(menubar)
        
        # Apply dark styling for focus
        self._apply_focus_styling(main_window, dark_theme=True)
    
    def _apply_immersive_focus(self, main_window):
        """Apply immersive focus: full-screen with ambient features"""
        # Apply deep focus first
        self._apply_deep_focus(main_window)
        
        # Go full screen
        main_window.showFullScreen()
        
        # Apply immersive styling
        self._apply_focus_styling(main_window, dark_theme=True, immersive=True)
    
    def _apply_focus_styling(self, main_window, dark_theme: bool = False, immersive: bool = False):
        """Apply focus-specific styling"""
        if dark_theme:
            focus_style = """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QScrollArea {
                background-color: #2d2d2d;
                border: none;
            }
            QLabel {
                background-color: #f8f8f8;
                border: 1px solid #333;
            }
            """
            
            if immersive:
                focus_style += """
                QWidget {
                    selection-background-color: #4a4a4a;
                }
                """
            
            main_window.setStyleSheet(focus_style)
    
    # Stage 5: Productivity tracking methods
    def record_page_read(self, time_spent: float):
        """Record page reading for productivity tracking"""
        if self.current_session:
            self.pages_read_in_session += 1
            self.current_session['pages_read'] = self.pages_read_in_session
            self.page_read_times.append(time_spent)
            self.last_activity_time = datetime.now()
    
    def record_interruption(self, interruption_type: str = "manual"):
        """Record an interruption during focus session"""
        if self.current_session:
            self.interruption_count += 1
            self.current_session['interruptions'] = self.interruption_count
            
            # Alert if too many interruptions
            if self.interruption_count >= 3:
                self.productivity_alert.emit(
                    "distraction",
                    f"Multiple interruptions detected ({self.interruption_count}). Consider deeper focus level?"
                )
    
    def _calculate_productivity_score(self) -> float:
        """Calculate productivity score for current session"""
        if not self.current_session:
            return 0.0
        
        score = 100.0
        
        # Deduct for interruptions
        interruption_penalty = min(self.interruption_count * 10, 40)
        score -= interruption_penalty
        
        # Deduct for slow reading (if we have data)
        if len(self.page_read_times) > 2:
            avg_time_per_page = sum(self.page_read_times) / len(self.page_read_times)
            if avg_time_per_page > 180:  # Slower than 3 minutes per page
                score -= 20
        
        # Bonus for consistent reading
        if len(self.page_read_times) > 3:
            import statistics
            try:
                mean_time = statistics.mean(self.page_read_times)
                std_dev = statistics.stdev(self.page_read_times)
                consistency = 100 - (std_dev / mean_time * 100) if mean_time > 0 else 0
                score += min(consistency * 0.2, 20)
            except:
                pass  # Skip if calculation fails
        
        return max(0, min(score, 100))
    
    def _calculate_average_reading_speed(self) -> float:
        """Calculate average reading speed for current session"""
        if not self.page_read_times:
            return 0.0
        return sum(self.page_read_times) / len(self.page_read_times)
    
    def _check_productivity_metrics(self):
        """Check and analyze productivity metrics"""
        if not self.current_session:
            return
        
        # Check reading speed
        if len(self.page_read_times) >= 3:  # Need some data
            recent_speeds = self.page_read_times[-3:]
            avg_speed = sum(recent_speeds) / len(recent_speeds)
            
            # Alert if reading speed drops significantly
            if len(self.page_read_times) > 6:
                earlier_speeds = self.page_read_times[-6:-3]
                earlier_avg = sum(earlier_speeds) / len(earlier_speeds)
                
                if avg_speed > earlier_avg * 1.5:  # 50% slower
                    self.productivity_alert.emit(
                        "speed_drop",
                        "Reading speed has decreased. Consider taking a short break?"
                    )
    
    def _check_idle_state(self):
        """Check for idle state indicating potential distraction"""
        if not self.current_session or not self.focus_settings.get('idle_detection', True):
            return
        
        time_since_activity = (datetime.now() - self.last_activity_time).total_seconds()
        idle_threshold = 120  # 2 minutes
        
        if time_since_activity > idle_threshold:
            self.record_interruption("idle_detected")
    
    def _suggest_break(self):
        """Suggest a break based on session length"""
        if self.current_session and self.session_start_time:
            session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
            
            if session_duration >= 25:  # Pomodoro length
                break_minutes = 5 if session_duration < 90 else 15
                self.break_recommendation.emit(break_minutes)
    
    def _save_focus_session_to_db(self, session_summary: dict):
        """Save focus session to database"""
        try:
            from database.models import db_manager
            
            db_manager.record_focus_session(
                topic_id=session_summary.get('topic_id'),
                document_id=session_summary.get('document_id'),
                start_time=self.session_start_time,
                end_time=datetime.now(),
                pages_read=session_summary.get('pages_read', 0),
                focus_level=session_summary.get('focus_level', 'standard'),
                productivity_score=session_summary.get('productivity_score', 0)
            )
            
        except Exception as e:
            print(f"❌ Error saving focus session to database: {e}")
    
    def get_focus_analytics(self, days: int = 30) -> dict:
        """Get focus session analytics for specified period"""
        try:
            from database.models import db_manager, FocusSession
            from datetime import datetime, timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            session = db_manager.get_session()
            try:
                # Get focus sessions in date range
                focus_sessions = session.query(FocusSession).filter(
                    FocusSession.start_time >= start_date,
                    FocusSession.was_focus_mode == True
                ).all()
                
                if not focus_sessions:
                    return {
                        'total_sessions': 0,
                        'total_focus_time': 0,
                        'average_session_length': 0,
                        'average_productivity_score': 0,
                        'most_productive_time': "09:00",
                        'interruption_rate': 0,
                        'consistency_score': 0
                    }
                
                # Calculate analytics
                total_sessions = len(focus_sessions)
                total_time = sum(s.duration or 0 for s in focus_sessions)
                avg_session_length = total_time / total_sessions if total_sessions > 0 else 0
                
                # Productivity scores
                productivity_scores = [s.productivity_score or 0 for s in focus_sessions if s.productivity_score]
                avg_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0
                
                # Find most productive time of day
                hour_productivity = {}
                for fs in focus_sessions:
                    hour = fs.start_time.hour
                    if hour not in hour_productivity:
                        hour_productivity[hour] = []
                    hour_productivity[hour].append(fs.productivity_score or 0)
                
                most_productive_hour = 9  # Default
                if hour_productivity:
                    most_productive_hour = max(
                        hour_productivity.keys(),
                        key=lambda h: sum(hour_productivity[h]) / len(hour_productivity[h])
                    )
                
                # Calculate interruption rate
                total_interruptions = sum(s.interruptions or 0 for s in focus_sessions)
                interruption_rate = total_interruptions / total_time if total_time > 0 else 0
                
                return {
                    'total_sessions': total_sessions,
                    'total_focus_time': total_time,
                    'average_session_length': avg_session_length,
                    'average_productivity_score': avg_productivity,
                    'most_productive_time': f"{most_productive_hour:02d}:00",
                    'interruption_rate': interruption_rate,
                    'consistency_score': self._calculate_consistency_score([s.duration for s in focus_sessions if s.duration])
                }
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error getting focus analytics: {e}")
            return {}
    
    def get_focus_recommendations(self) -> List[str]:
        """Get personalized focus recommendations based on analytics"""
        analytics = self.get_focus_analytics(7)  # Last week
        recommendations = []
        
        if analytics.get('total_sessions', 0) == 0:
            recommendations.append("Start with 25-minute focus sessions to build the habit")
            recommendations.append("Try the Standard focus level to minimize distractions")
            return recommendations
        
        # Session length recommendations
        avg_length = analytics.get('average_session_length', 0)
        if avg_length < 15:
            recommendations.append("Try extending sessions to 25+ minutes for deeper focus")
        elif avg_length > 90:
            recommendations.append("Consider shorter sessions with breaks to maintain quality")
        
        # Productivity recommendations
        avg_productivity = analytics.get('average_productivity_score', 0)
        if avg_productivity < 60:
            recommendations.append("Try Deep focus level to eliminate more distractions")
            recommendations.append("Consider ambient sounds or background music")
        
        # Interruption recommendations
        interruption_rate = analytics.get('interruption_rate', 0)
        if interruption_rate > 0.1:  # More than 1 interruption per 10 minutes
            recommendations.append("Try Immersive mode to minimize external distractions")
            recommendations.append("Put devices in Do Not Disturb mode during focus sessions")
        
        # Timing recommendations
        most_productive_time = analytics.get('most_productive_time')
        if most_productive_time:
            recommendations.append(
                f"Schedule important reading during your peak time: {most_productive_time}"
            )
        
        return recommendations or ["Keep up the great focus work!"]
    
    def _calculate_consistency_score(self, durations: List[float]) -> float:
        """Calculate consistency score from session durations"""
        if len(durations) < 3:
            return 0.0
        
        try:
            import statistics
            std_dev = statistics.stdev(durations)
            mean_duration = statistics.mean(durations)
            # Lower std dev relative to mean = higher consistency
            consistency = max(0, 100 - (std_dev / mean_duration * 100)) if mean_duration > 0 else 0
            return min(consistency, 100)
        except:
            return 50.0  # Default moderate score
    
    def get_current_session_info(self) -> Optional[dict]:
        """Get current session information"""
        if not self.current_session or not self.session_start_time:
            return None
        
        duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        
        return {
            'session_id': self.current_session['id'],
            'duration': duration,
            'pages_read': self.pages_read_in_session,
            'interruptions': self.interruption_count,
            'focus_level': self.current_session['focus_level'].value,
            'productivity_score': self._calculate_productivity_score(),
            'is_active': True
        }
    
    # Existing helper methods
    def _hide_widget(self, widget: QWidget):
        """Hide widget and track for restoration"""
        if widget and widget.isVisible():
            self.original_states[widget] = widget.isVisible()
            self.hidden_widgets.append(widget)
            widget.hide()
    
    def _restore_hidden_widgets(self):
        """Restore all hidden widgets"""
        for widget in self.hidden_widgets:
            if widget:
                widget.show()
        
        self.hidden_widgets = []
        self.original_states = {}
    
    def update_setting(self, key: str, value):
        """Update a focus setting"""
        if key in self.focus_settings:
            self.focus_settings[key] = value
            self._save_settings()
            self.settings_changed.emit(self.focus_settings)
    
    def get_settings(self) -> Dict:
        """Get current focus settings"""
        return self.focus_settings.copy()
    
    def is_enabled(self) -> bool:
        """Check if focus mode is currently enabled"""
        return self.is_focus_mode
    
    def _load_settings(self):
        """Load focus settings from storage"""
        for key, default_value in self.focus_settings.items():
            value = self.settings.value(key, default_value, type=type(default_value))
            self.focus_settings[key] = value
    
    def _save_settings(self):
        """Save focus settings to storage"""
        for key, value in self.focus_settings.items():
            self.settings.setValue(key, value)