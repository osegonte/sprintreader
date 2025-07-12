"""
Pomodoro Timer Implementation
25-minute focus sessions with breaks
"""

from qt_compat import QObject, QTimer, pyqtSignal
from datetime import datetime
from typing import Dict, List

class PomodoroSession:
    """Represents a single Pomodoro session"""
    
    def __init__(self, start_time: datetime, duration: int):
        self.start_time = start_time
        self.duration = duration  # in minutes
        self.end_time = None
        self.completed = False
        self.interruptions = 0
    
    def complete(self):
        """Mark session as completed"""
        self.end_time = datetime.now()
        self.completed = True
    
    def add_interruption(self):
        """Record an interruption"""
        self.interruptions += 1

class PomodoroTimer(QObject):
    """Dedicated Pomodoro timer with cycle tracking"""
    
    # Signals
    session_started = pyqtSignal(int)  # session number
    session_completed = pyqtSignal(int)  # session number
    break_started = pyqtSignal(bool, int)  # is_long_break, duration
    cycle_completed = pyqtSignal(int)  # cycle number (4 sessions)
    
    def __init__(self):
        super().__init__()
        
        # Pomodoro settings
        self.work_duration = 25  # minutes
        self.short_break = 5     # minutes
        self.long_break = 15     # minutes
        self.sessions_per_cycle = 4
        
        # State tracking
        self.current_cycle = 0
        self.current_session = 0
        self.sessions_today = []
        self.total_sessions = 0
        
        # Statistics
        self.daily_stats = {
            'sessions_completed': 0,
            'total_focus_time': 0,  # minutes
            'interruptions': 0,
            'cycles_completed': 0
        }
    
    def start_new_cycle(self) -> int:
        """Start a new Pomodoro cycle"""
        self.current_cycle += 1
        self.current_session = 0
        return self.current_cycle
    
    def start_session(self) -> PomodoroSession:
        """Start a new Pomodoro session"""
        self.current_session += 1
        session = PomodoroSession(datetime.now(), self.work_duration)
        self.sessions_today.append(session)
        
        self.session_started.emit(self.current_session)
        return session
    
    def complete_session(self):
        """Complete current session"""
        if self.sessions_today:
            current = self.sessions_today[-1]
            current.complete()
            
            # Update stats
            self.daily_stats['sessions_completed'] += 1
            self.daily_stats['total_focus_time'] += self.work_duration
            self.total_sessions += 1
            
            self.session_completed.emit(self.current_session)
            
            # Check if cycle is complete
            if self.current_session >= self.sessions_per_cycle:
                self.daily_stats['cycles_completed'] += 1
                self.cycle_completed.emit(self.current_cycle)
                self.start_new_cycle()
    
    def start_break(self) -> tuple:
        """Start appropriate break (short or long)"""
        is_long_break = (self.current_session % self.sessions_per_cycle) == 0
        duration = self.long_break if is_long_break else self.short_break
        
        self.break_started.emit(is_long_break, duration)
        return is_long_break, duration
    
    def add_interruption(self):
        """Record an interruption in current session"""
        if self.sessions_today:
            self.sessions_today[-1].add_interruption()
            self.daily_stats['interruptions'] += 1
    
    def get_today_stats(self) -> Dict:
        """Get today's Pomodoro statistics"""
        return self.daily_stats.copy()
    
    def get_session_history(self) -> List[PomodoroSession]:
        """Get list of today's sessions"""
        return self.sessions_today.copy()
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)"""
        self.daily_stats = {
            'sessions_completed': 0,
            'total_focus_time': 0,
            'interruptions': 0,
            'cycles_completed': 0
        }
        self.sessions_today = []
        self.current_cycle = 0
        self.current_session = 0
