"""
Sprint Timer Implementation
Quick 5-minute reading bursts
"""

from qt_compat import QObject, pyqtSignal
from datetime import datetime
from typing import List, Dict

class SprintSession:
    """Represents a single Sprint session"""
    
    def __init__(self, duration: int = 5):
        self.start_time = datetime.now()
        self.duration = duration  # minutes
        self.end_time = None
        self.pages_read = 0
        self.completed = False
        self.goal_achieved = False
    
    def complete(self, pages_read: int = 0):
        """Complete the sprint session"""
        self.end_time = datetime.now()
        self.pages_read = pages_read
        self.completed = True
        # Goal is typically 2-3 pages in 5 minutes
        self.goal_achieved = pages_read >= 2
    
    def get_actual_duration(self) -> float:
        """Get actual duration in minutes"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 60
        return 0

class SprintTimer(QObject):
    """Sprint timer for quick reading sessions"""
    
    # Signals
    sprint_started = pyqtSignal(int)  # duration in minutes
    sprint_completed = pyqtSignal(bool)  # goal_achieved
    goal_updated = pyqtSignal(int)  # new goal
    
    def __init__(self):
        super().__init__()
        
        # Sprint settings
        self.default_duration = 5  # minutes
        self.page_goal = 2  # pages per 5-minute sprint
        
        # State tracking
        self.sprints_today = []
        self.current_sprint = None
        self.total_sprints = 0
        
        # Statistics
        self.daily_stats = {
            'sprints_completed': 0,
            'total_pages': 0,
            'goals_achieved': 0,
            'average_pages_per_sprint': 0.0,
            'total_sprint_time': 0  # minutes
        }
    
    def start_sprint(self, duration: int = None) -> SprintSession:
        """Start a new sprint session"""
        if duration is None:
            duration = self.default_duration
        
        self.current_sprint = SprintSession(duration)
        self.sprint_started.emit(duration)
        return self.current_sprint
    
    def complete_sprint(self, pages_read: int = 0):
        """Complete current sprint session"""
        if self.current_sprint:
            self.current_sprint.complete(pages_read)
            self.sprints_today.append(self.current_sprint)
            
            # Update statistics
            self.daily_stats['sprints_completed'] += 1
            self.daily_stats['total_pages'] += pages_read
            self.daily_stats['total_sprint_time'] += self.current_sprint.get_actual_duration()
            
            if self.current_sprint.goal_achieved:
                self.daily_stats['goals_achieved'] += 1
            
            # Calculate average
            if self.daily_stats['sprints_completed'] > 0:
                self.daily_stats['average_pages_per_sprint'] = (
                    self.daily_stats['total_pages'] / self.daily_stats['sprints_completed']
                )
            
            self.total_sprints += 1
            self.sprint_completed.emit(self.current_sprint.goal_achieved)
            self.current_sprint = None
    
    def set_page_goal(self, pages: int):
        """Set pages goal for sprints"""
        self.page_goal = pages
        self.goal_updated.emit(pages)
    
    def get_current_goal(self) -> int:
        """Get current page goal"""
        return self.page_goal
    
    def get_today_stats(self) -> Dict:
        """Get today's sprint statistics"""
        return self.daily_stats.copy()
    
    def get_sprint_history(self) -> List[SprintSession]:
        """Get list of today's sprints"""
        return self.sprints_today.copy()
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.daily_stats['sprints_completed'] > 0:
            return (self.daily_stats['goals_achieved'] / 
                   self.daily_stats['sprints_completed']) * 100
        return 0.0
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_stats = {
            'sprints_completed': 0,
            'total_pages': 0,
            'goals_achieved': 0,
            'average_pages_per_sprint': 0.0,
            'total_sprint_time': 0
        }
        self.sprints_today = []
