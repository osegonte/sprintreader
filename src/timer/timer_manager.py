"""
Timer Manager - Coordinates different timer modes
"""

from enum import Enum
from typing import Optional, Callable
from qt_compat import QObject, QTimer, pyqtSignal
from datetime import datetime, timedelta

class TimerMode(Enum):
    POMODORO = "pomodoro"
    SPRINT = "sprint"
    CUSTOM = "custom"
    REGULAR = "regular"

class TimerState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    BREAK = "break"

class TimerManager(QObject):
    """Central timer management for all reading sessions"""
    
    # Signals
    timer_started = pyqtSignal(str)  # mode
    timer_paused = pyqtSignal()
    timer_resumed = pyqtSignal()
    timer_stopped = pyqtSignal()
    timer_finished = pyqtSignal(str)  # mode
    break_started = pyqtSignal(int)  # break duration
    break_finished = pyqtSignal()
    time_updated = pyqtSignal(int)  # remaining seconds
    
    def __init__(self):
        super().__init__()
        self.current_mode = TimerMode.REGULAR
        self.state = TimerState.STOPPED
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        
        # Timer settings
        self.session_duration = 25 * 60  # 25 minutes in seconds
        self.break_duration = 5 * 60     # 5 minutes in seconds
        self.long_break_duration = 15 * 60  # 15 minutes in seconds
        
        # State tracking
        self.remaining_time = 0
        self.session_count = 0
        self.is_break_time = False
        self.start_time = None
    
    def start_pomodoro(self) -> bool:
        """Start a Pomodoro session (25 min focus + 5 min break)"""
        if self.state == TimerState.RUNNING:
            return False
        
        self.current_mode = TimerMode.POMODORO
        self.session_duration = 25 * 60  # 25 minutes
        self._start_session()
        return True
    
    def start_sprint(self) -> bool:
        """Start a Sprint session (5 min quick reading)"""
        if self.state == TimerState.RUNNING:
            return False
        
        self.current_mode = TimerMode.SPRINT
        self.session_duration = 5 * 60  # 5 minutes
        self._start_session()
        return True
    
    def start_custom(self, duration_minutes: int) -> bool:
        """Start a custom duration session"""
        if self.state == TimerState.RUNNING:
            return False
        
        self.current_mode = TimerMode.CUSTOM
        self.session_duration = duration_minutes * 60
        self._start_session()
        return True
    
    def pause(self):
        """Pause current timer"""
        if self.state == TimerState.RUNNING:
            self.timer.stop()
            self.state = TimerState.PAUSED
            self.timer_paused.emit()
    
    def resume(self):
        """Resume paused timer"""
        if self.state == TimerState.PAUSED:
            self.timer.start(1000)  # 1 second intervals
            self.state = TimerState.RUNNING
            self.timer_resumed.emit()
    
    def stop(self):
        """Stop current timer"""
        self.timer.stop()
        self.state = TimerState.STOPPED
        self.is_break_time = False
        self.remaining_time = 0
        self.timer_stopped.emit()
    
    def get_remaining_time(self) -> int:
        """Get remaining time in seconds"""
        return self.remaining_time
    
    def get_formatted_time(self) -> str:
        """Get formatted time string (MM:SS)"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_current_mode(self) -> TimerMode:
        """Get current timer mode"""
        return self.current_mode
    
    def get_state(self) -> TimerState:
        """Get current timer state"""
        return self.state
    
    def is_running(self) -> bool:
        """Check if timer is currently running"""
        return self.state == TimerState.RUNNING
    
    def _start_session(self):
        """Internal method to start a timer session"""
        self.remaining_time = self.session_duration
        self.start_time = datetime.now()
        self.state = TimerState.RUNNING
        self.is_break_time = False
        
        self.timer.start(1000)  # Update every second
        self.timer_started.emit(self.current_mode.value)
    
    def _on_timer_tick(self):
        """Handle timer tick (every second)"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.time_updated.emit(self.remaining_time)
        else:
            # Timer finished
            self.timer.stop()
            self._handle_timer_completion()
    
    def _handle_timer_completion(self):
        """Handle timer completion - start break or finish"""
        if not self.is_break_time and self.current_mode == TimerMode.POMODORO:
            # Pomodoro session finished, start break
            self.session_count += 1
            self.is_break_time = True
            
            # Determine break duration (long break every 4 sessions)
            if self.session_count % 4 == 0:
                break_duration = self.long_break_duration
            else:
                break_duration = self.break_duration
            
            self.remaining_time = break_duration
            self.state = TimerState.BREAK
            self.timer.start(1000)
            self.break_started.emit(break_duration)
            
        elif self.is_break_time:
            # Break finished
            self.state = TimerState.STOPPED
            self.is_break_time = False
            self.break_finished.emit()
            
        else:
            # Sprint or Custom session finished
            self.state = TimerState.STOPPED
            self.timer_finished.emit(self.current_mode.value)
