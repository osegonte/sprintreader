"""
Notification Manager - Local notifications and reminders
"""

import platform
import subprocess
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from qt_compat import QObject, QTimer, pyqtSignal

class NotificationManager(QObject):
    """Manages local notifications and reading reminders"""
    
    # Signals
    notification_sent = pyqtSignal(str)  # message
    reminder_triggered = pyqtSignal(str)  # reminder type
    
    def __init__(self):
        super().__init__()
        self.system = platform.system()
        self.notification_history = []
        
        # Reminder timer
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(60000)  # Check every minute
        
        # Settings
        self.notifications_enabled = True
        self.reminder_settings = {
            'daily_goal_reminder': True,
            'session_break_reminder': True,
            'streak_maintenance_reminder': True,
            'comeback_reminder': True
        }
        
        # State tracking
        self.last_session_time = None
        self.daily_goal_reminded = False
    
    def send_notification(self, title: str, message: str, urgency: str = "normal"):
        """Send a local notification"""
        if not self.notifications_enabled:
            return
        
        try:
            if self.system == "Darwin":  # macOS
                self._send_macos_notification(title, message)
            elif self.system == "Linux":
                self._send_linux_notification(title, message, urgency)
            elif self.system == "Windows":
                self._send_windows_notification(title, message)
            
            # Log notification
            self.notification_history.append({
                'timestamp': datetime.now(),
                'title': title,
                'message': message,
                'urgency': urgency
            })
            
            self.notification_sent.emit(f"{title}: {message}")
            
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
    
    def _send_macos_notification(self, title: str, message: str):
        """Send notification on macOS using osascript"""
        script = f'''
        display notification "{message}" with title "{title}" sound name "Glass"
        '''
        subprocess.run(['osascript', '-e', script], check=True)
    
    def _send_linux_notification(self, title: str, message: str, urgency: str):
        """Send notification on Linux using notify-send"""
        subprocess.run([
            'notify-send',
            '-u', urgency,
            '-i', 'document-open',
            title,
            message
        ], check=True)
    
    def _send_windows_notification(self, title: str, message: str):
        """Send notification on Windows using PowerShell"""
        script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = "{title}"
        $notify.BalloonTipText = "{message}"
        $notify.Visible = $true
        $notify.ShowBalloonTip(3000)
        '''
        subprocess.run(['powershell', '-Command', script], check=True)
    
    def send_timer_notification(self, timer_type: str, action: str):
        """Send timer-specific notifications"""
        notifications = {
            'pomodoro_complete': {
                'title': '🍅 Pomodoro Complete!',
                'message': 'Great focus! Time for a 5-minute break.'
            },
            'break_complete': {
                'title': '⏰ Break Over',
                'message': 'Ready for another focused session?'
            },
            'sprint_complete': {
                'title': '⚡ Sprint Complete!',
                'message': 'Quick reading session finished. How did it go?'
            },
            'long_break': {
                'title': '🧘‍♀️ Long Break Time',
                'message': 'You\'ve earned a 15-minute break!'
            }
        }
        
        key = f"{timer_type}_{action}"
        if key in notifications:
            notif = notifications[key]
            self.send_notification(notif['title'], notif['message'])
    
    def send_goal_reminder(self, goal_type: str, progress: float):
        """Send goal progress reminders"""
        if goal_type == "daily_reading" and progress < 50 and not self.daily_goal_reminded:
            self.send_notification(
                "📚 Daily Reading Goal",
                f"You're {progress:.0f}% toward your daily goal. Keep going!"
            )
            self.daily_goal_reminded = True
    
    def send_streak_reminder(self, streak_days: int, at_risk: bool = False):
        """Send streak maintenance reminders"""
        if at_risk and streak_days > 0:
            self.send_notification(
                f"🔥 {streak_days}-Day Streak at Risk!",
                "Don't break your reading streak. Start a quick session?"
            )
        elif streak_days > 0 and streak_days % 7 == 0:
            self.send_notification(
                f"🎉 {streak_days}-Day Streak!",
                "Amazing consistency! Keep up the great work."
            )
    
    def send_comeback_reminder(self, days_since_last: int):
        """Send comeback reminder for inactive users"""
        if days_since_last >= 2:
            messages = {
                2: "📖 Ready to dive back into reading?",
                3: "📚 Your books are waiting for you!",
                7: "🔖 It's been a week - time to get back to reading?",
                14: "📖 Two weeks away - let's restart your reading habit!"
            }
            
            message = messages.get(days_since_last, "📚 Welcome back! Ready to read?")
            self.send_notification("SprintReader", message)
    
    def _check_reminders(self):
        """Check if any reminders should be triggered"""
        now = datetime.now()
        
        # Check daily goal reminder (afternoon)
        if (now.hour == 15 and now.minute == 0 and 
            self.reminder_settings.get('daily_goal_reminder', True)):
            self.reminder_triggered.emit('daily_goal')
        
        # Check streak maintenance (evening)
        if (now.hour == 20 and now.minute == 0 and 
            self.reminder_settings.get('streak_maintenance_reminder', True)):
            self.reminder_triggered.emit('streak_maintenance')
        
        # Reset daily flags at midnight
        if now.hour == 0 and now.minute == 0:
            self.daily_goal_reminded = False
    
    def set_last_session_time(self, session_time: datetime):
        """Update last session time for comeback reminders"""
        self.last_session_time = session_time
    
    def enable_notifications(self, enabled: bool):
        """Enable or disable notifications"""
        self.notifications_enabled = enabled
    
    def update_reminder_setting(self, setting: str, enabled: bool):
        """Update specific reminder setting"""
        if setting in self.reminder_settings:
            self.reminder_settings[setting] = enabled
    
    def get_notification_history(self) -> List[Dict]:
        """Get recent notification history"""
        return self.notification_history[-50:]  # Last 50 notifications
    
    def clear_notification_history(self):
        """Clear notification history"""
        self.notification_history = []
