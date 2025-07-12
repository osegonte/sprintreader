"""
Stage 3 Database Models
Additional tables for timer modes, focus sessions, and analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from .models import Base

class TimerSession(Base):
    """Timer-based reading sessions (Pomodoro, Sprint, Custom)"""
    __tablename__ = 'timer_sessions'
    
    id = Column(Integer, primary_key=True)
    reading_session_id = Column(Integer, ForeignKey('reading_sessions.id'))
    timer_mode = Column(String(50), nullable=False)  # 'pomodoro', 'sprint', 'custom'
    planned_duration = Column(Integer)  # minutes
    actual_duration = Column(Float)  # actual minutes
    interruptions = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    break_taken = Column(Boolean, default=False)
    break_duration = Column(Integer)  # minutes
    focus_rating = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    reading_session = relationship("ReadingSession", backref="timer_session")

class FocusSession(Base):
    """Focus mode sessions and settings"""
    __tablename__ = 'focus_sessions'
    
    id = Column(Integer, primary_key=True)
    reading_session_id = Column(Integer, ForeignKey('reading_sessions.id'))
    focus_mode_enabled = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    distractions_blocked = Column(Integer, default=0)
    settings_used = Column(JSON)  # Store focus settings as JSON
    effectiveness_rating = Column(Integer)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    reading_session = relationship("ReadingSession", backref="focus_session")

class UserGoal(Base):
    """User-defined reading goals"""
    __tablename__ = 'user_goals'
    
    id = Column(Integer, primary_key=True)
    goal_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
    metric_type = Column(String(50), nullable=False)  # 'time', 'pages', 'sessions'
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_achieved = Column(Boolean, default=False)
    achievement_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserStreak(Base):
    """Reading streak tracking"""
    __tablename__ = 'user_streaks'
    
    id = Column(Integer, primary_key=True)
    streak_type = Column(String(50), default='daily')  # 'daily', 'weekly'
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime)
    streak_start_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserReflection(Base):
    """End-of-session reflections and feedback"""
    __tablename__ = 'user_reflections'
    
    id = Column(Integer, primary_key=True)
    reading_session_id = Column(Integer, ForeignKey('reading_sessions.id'))
    focus_rating = Column(Integer)  # 1-5 scale
    energy_level = Column(Integer)  # 1-5 scale
    comprehension_rating = Column(Integer)  # 1-5 scale
    distraction_notes = Column(Text)
    key_insights = Column(Text)
    session_mood = Column(String(50))  # 'focused', 'distracted', 'tired', etc.
    would_repeat_setup = Column(Boolean)
    improvement_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    reading_session = relationship("ReadingSession", backref="reflection")

class NotificationLog(Base):
    """Log of sent notifications"""
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255))
    message = Column(Text)
    recipient = Column(String(100), default='user')
    sent_at = Column(DateTime, default=datetime.utcnow)
    was_clicked = Column(Boolean, default=False)
    action_taken = Column(String(100))  # What user did after notification

# Update existing models with new relationships
def extend_existing_models():
    """Add new columns to existing models for Stage 3"""
    # These would typically be handled by database migrations
    # For now, we'll document the additions needed:
    
    # ReadingSession additions:
    # - session_rating (Integer) # 1-5 scale
    # - mood_before (String) # User's mood before session
    # - mood_after (String) # User's mood after session
    # - environment_notes (Text) # Notes about reading environment
    
    # Document additions:
    # - difficulty_rating (Integer) # 1-5 scale
    # - genre (String) # Document genre/category
    # - priority_level (Integer) # 1-5 priority
    # - target_completion_date (DateTime)
    
    # Settings additions for Stage 3:
    stage3_settings = [
        ('pomodoro_work_duration', '25'),
        ('pomodoro_break_duration', '5'),
        ('pomodoro_long_break_duration', '15'),
        ('sprint_duration', '5'),
        ('sprint_page_goal', '2'),
        ('focus_mode_auto_enable', 'false'),
        ('notifications_enabled', 'true'),
        ('daily_reading_goal', '30'),  # minutes
        ('weekly_reading_goal', '210'),  # minutes (30 * 7)
        ('streak_notification_enabled', 'true'),
        ('end_session_reflection_prompt', 'true')
    ]
    
    return stage3_settings
