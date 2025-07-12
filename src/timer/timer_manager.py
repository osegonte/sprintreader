"""
Timer Manager - Coordinates different timer modes (ENHANCED VERSION)
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
    """Central timer management for all reading sessions - ENHANCED"""
    
    # Signals - ENHANCED
    timer_started = pyqtSignal(str)  # mode
    timer_paused = pyqtSignal()
    timer_resumed = pyqtSignal()
    timer_stopped = pyqtSignal()
    timer_finished = pyqtSignal(str)  # mode
    break_started = pyqtSignal(int)  # break duration in seconds
    break_finished = pyqtSignal()
    time_updated = pyqtSignal(int)  # remaining seconds
    
    def __init__(self):
        super().__init__()
        print("🔧 Initializing TimerManager...")
        
        self.current_mode = TimerMode.REGULAR
        self.state = TimerState.STOPPED
        
        # Create and configure timer - ENHANCED
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.setSingleShot(False)  # Ensure repeating timer
        
        # Timer settings (all in seconds for consistency)
        self.work_duration = 25 * 60      # 25 minutes in seconds
        self.sprint_duration = 5 * 60     # 5 minutes in seconds
        self.break_duration = 5 * 60      # 5 minutes in seconds
        self.long_break_duration = 15 * 60  # 15 minutes in seconds
        
        # State tracking - ENHANCED
        self.remaining_time = 0
        self.session_count = 0
        self.is_break_time = False
        self.start_time = None
        self.total_duration = 0  # Track original duration
        
        print("✅ TimerManager initialized")
    
    def start_pomodoro(self) -> bool:
        """Start a Pomodoro session (25 min focus + 5 min break)"""
        print("🍅 Starting Pomodoro session...")
        
        if self.state != TimerState.STOPPED:
            print("⚠️ Timer already running or paused")
            return False
        
        self.current_mode = TimerMode.POMODORO
        self.total_duration = self.work_duration
        self._start_session()
        return True
    
    def start_sprint(self) -> bool:
        """Start a Sprint session (5 min quick reading)"""
        print("⚡ Starting Sprint session...")
        
        if self.state != TimerState.STOPPED:
            print("⚠️ Timer already running or paused")
            return False
        
        self.current_mode = TimerMode.SPRINT
        self.total_duration = self.sprint_duration
        self._start_session()
        return True
    
    def start_custom(self, duration_minutes: int) -> bool:
        """Start a custom duration session"""
        print(f"⏱️ Starting Custom session: {duration_minutes} minutes...")
        
        if self.state != TimerState.STOPPED:
            print("⚠️ Timer already running or paused")
            return False
        
        self.current_mode = TimerMode.CUSTOM
        self.total_duration = duration_minutes * 60  # Convert to seconds
        self._start_session()
        return True
    
    def pause(self):
        """Pause current timer"""
        print("⏸️ Pausing timer...")
        
        if self.state == TimerState.RUNNING:
            self.timer.stop()
            self.state = TimerState.PAUSED
            self.timer_paused.emit()
            print("✅ Timer paused")
        else:
            print("⚠️ Timer not running, cannot pause")
    
    def resume(self):
        """Resume paused timer"""
        print("▶️ Resuming timer...")
        
        if self.state == TimerState.PAUSED:
            self.timer.start(1000)  # 1 second intervals
            self.state = TimerState.RUNNING
            self.timer_resumed.emit()
            print("✅ Timer resumed")
        else:
            print("⚠️ Timer not paused, cannot resume")
    
    def stop(self):
        """Stop current timer"""
        print("⏹️ Stopping timer...")
        
        self.timer.stop()
        self.state = TimerState.STOPPED
        self.is_break_time = False
        self.remaining_time = 0
        self.total_duration = 0
        self.timer_stopped.emit()
        print("✅ Timer stopped")
    
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
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage (0-100)"""
        if self.total_duration <= 0:
            return 0.0
        return ((self.total_duration - self.remaining_time) / self.total_duration) * 100
    
    def _start_session(self):
        """Internal method to start a timer session - ENHANCED"""
        print(f"🎬 Starting session: {self.current_mode.value}")
        
        self.remaining_time = self.total_duration
        self.start_time = datetime.now()
        self.state = TimerState.RUNNING
        self.is_break_time = False
        
        # Start the QTimer with 1-second intervals
        self.timer.start(1000)
        
        # Emit signals
        self.timer_started.emit(self.current_mode.value)
        self.time_updated.emit(self.remaining_time)
        
        print(f"✅ Session started: {self.get_formatted_time()}")
    
    def _on_timer_tick(self):
        """Handle timer tick (every second) - ENHANCED"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.time_updated.emit(self.remaining_time)
            
            # Debug output every 10 seconds
            if self.remaining_time % 10 == 0:
                print(f"⏰ Timer tick: {self.get_formatted_time()} remaining")
        else:
            # Timer finished
            print("⏰ Timer reached zero")
            self.timer.stop()
            self._handle_timer_completion()
    
    def _handle_timer_completion(self):
        """Handle timer completion - start break or finish - ENHANCED"""
        print(f"🏁 Timer completion - Mode: {self.current_mode.value}, Break: {self.is_break_time}")
        
        if not self.is_break_time and self.current_mode == TimerMode.POMODORO:
            # Pomodoro work session finished, start break
            print("🍅 Pomodoro work session complete, starting break...")
            
            self.session_count += 1
            self.is_break_time = True
            
            # Determine break duration (long break every 4 sessions)
            if self.session_count % 4 == 0:
                break_duration = self.long_break_duration
                print(f"🛌 Long break time: {break_duration // 60} minutes")
            else:
                break_duration = self.break_duration
                print(f"☕ Short break time: {break_duration // 60} minutes")
            
            # Start break timer
            self.remaining_time = break_duration
            self.total_duration = break_duration
            self.state = TimerState.BREAK
            self.timer.start(1000)
            
            # Emit signals
            self.break_started.emit(break_duration)
            self.time_updated.emit(self.remaining_time)
            
        elif self.is_break_time:
            # Break finished
            print("☕ Break finished")
            self.state = TimerState.STOPPED
            self.is_break_time = False
            self.remaining_time = 0
            self.total_duration = 0
            self.break_finished.emit()
            
        else:
            # Sprint or Custom session finished, or Pomodoro without break
            print(f"🎯 {self.current_mode.value} session finished")
            self.state = TimerState.STOPPED
            self.remaining_time = 0
            self.total_duration = 0
            self.timer_finished.emit(self.current_mode.value)
    
    def get_session_info(self) -> dict:
        """Get detailed session information"""
        return {
            'mode': self.current_mode.value,
            'state': self.state.value,
            'remaining_time': self.remaining_time,
            'formatted_time': self.get_formatted_time(),
            'progress_percentage': self.get_progress_percentage(),
            'is_break_time': self.is_break_time,
            'session_count': self.session_count,
            'start_time': self.start_time.isoformat() if self.start_time else None
        }
    
    def reset_session_count(self):
        """Reset session count (useful for new day)"""
        self.session_count = 0
        print("🔄 Session count reset")