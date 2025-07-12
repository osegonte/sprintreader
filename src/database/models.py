"""
SprintReader Database Models - Enhanced with Stage 5 Features
SQLAlchemy ORM models for the application with Topic-Based Organization & Goals
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    Float, ForeignKey, create_engine, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()

# STAGE 5: New Tables for Topic Organization and Goal Setting

class Topic(Base):
    """Topics for organizing PDFs and notes - Stage 5"""
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    color = Column(String(7), default='#7E22CE')  # Hex color
    icon = Column(String(50), default='📚')  # Emoji or icon
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="topic")
    goals = relationship("Goal", back_populates="topic")

class Goal(Base):
    """Reading goals for topics or individual documents - Stage 5"""
    __tablename__ = 'goals'
    
    id = Column(Integer, primary_key=True)
    
    # Goal can be for topic OR document (not both)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Goal details
    goal_type = Column(String(50), nullable=False)  # 'time', 'pages', 'deadline'
    target_value = Column(Float, nullable=False)  # Target minutes, pages, etc.
    target_date = Column(DateTime, nullable=True)  # For deadline goals
    
    # Progress tracking
    current_value = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)
    
    # Adaptive settings - Stage 5 enhancement
    daily_target = Column(Float)  # Auto-calculated daily target
    original_target = Column(Float)  # Store original target for adjustments
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = relationship("Topic", back_populates="goals")
    document = relationship("Document", back_populates="goals")

class FocusSession(Base):
    """Focus mode sessions with enhanced tracking - Stage 5"""
    __tablename__ = 'focus_sessions'
    
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)  # in minutes
    pages_read = Column(Integer, default=0)
    
    # Focus mode specific - Stage 5
    was_focus_mode = Column(Boolean, default=False)
    focus_level = Column(String(20))  # 'minimal', 'standard', 'deep', 'immersive'
    interruptions = Column(Integer, default=0)
    productivity_score = Column(Float)  # 0-100 based on focus metrics
    
    created_at = Column(DateTime, default=datetime.utcnow)

class UserStreak(Base):
    """Track daily reading streaks - Stage 5"""
    __tablename__ = 'user_streaks'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, unique=True)
    minutes_read = Column(Float, default=0.0)
    pages_read = Column(Integer, default=0)
    sessions_count = Column(Integer, default=0)
    goals_worked_on = Column(Integer, default=0)
    
    # Streak calculation
    is_streak_day = Column(Boolean, default=False)  # Met minimum requirement
    streak_number = Column(Integer, default=0)  # Current streak length
    
    created_at = Column(DateTime, default=datetime.utcnow)

# EXISTING MODELS - Enhanced with Stage 5 relationships

class Document(Base):
    """PDF documents being read - Enhanced for Stage 5"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    title = Column(String(255))
    total_pages = Column(Integer)
    current_page = Column(Integer, default=1)
    total_reading_time = Column(Float, default=0.0)  # in minutes
    estimated_reading_time = Column(Float)  # estimated total time
    reading_speed = Column(Float)  # pages per minute
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Stage 5: Topic relationship
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=True)
    
    # Relationships
    topic = relationship("Topic", back_populates="documents")
    reading_sessions = relationship("ReadingSession", back_populates="document")
    notes = relationship("Note", back_populates="document")
    goals = relationship("Goal", back_populates="document")

class ReadingSession(Base):
    """Individual reading sessions - Enhanced for Stage 5"""
    __tablename__ = 'reading_sessions'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)  # in minutes
    pages_read = Column(Integer, default=0)
    start_page = Column(Integer)
    end_page = Column(Integer)
    session_type = Column(String(50))  # 'pomodoro', 'sprint', 'regular'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stage 5: Enhanced tracking
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=True)
    goal_id = Column(Integer, ForeignKey('goals.id'), nullable=True)
    focus_mode = Column(Boolean, default=False)
    productivity_score = Column(Float)  # Link to focus session data
    
    # Relationships
    document = relationship("Document", back_populates="reading_sessions")

class Note(Base):
    """Notes and highlights from PDFs - Enhanced for Stage 5"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    page_number = Column(Integer, nullable=False)
    highlighted_text = Column(Text)
    note_content = Column(Text)
    topic = Column(String(255))  # Keep for backward compatibility
    x_position = Column(Float)  # for highlight positioning
    y_position = Column(Float)
    width = Column(Float)
    height = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Stage 5: Enhanced note organization
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=True)
    tags = Column(JSON)  # Store tags as JSON array
    
    # Relationships
    document = relationship("Document", back_populates="notes")

class Settings(Base):
    """Application settings - Enhanced for Stage 5"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database connection and session management
class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables including Stage 5 enhancements"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully (including Stage 5)")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all tables (use with caution)"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️  All tables dropped")
    
    # Stage 5: Enhanced database operations
    def get_or_create_topic(self, name: str, description: str = "", color: str = "#7E22CE") -> int:
        """Get existing topic or create new one"""
        session = self.get_session()
        try:
            # Try to find existing topic
            topic = session.query(Topic).filter_by(name=name).first()
            
            if not topic:
                topic = Topic(
                    name=name,
                    description=description,
                    color=color
                )
                session.add(topic)
                session.commit()
                print(f"✅ Created new topic: {name}")
            
            return topic.id
            
        except Exception as e:
            print(f"❌ Error with topic: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def assign_document_to_topic(self, document_id: int, topic_id: int) -> bool:
        """Assign document to a topic"""
        session = self.get_session()
        try:
            document = session.query(Document).filter_by(id=document_id).first()
            if document:
                document.topic_id = topic_id
                document.updated_at = datetime.utcnow()
                session.commit()
                print(f"✅ Document {document_id} assigned to topic {topic_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error assigning document to topic: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def create_goal(self, goal_type: str, target_value: float, 
                   topic_id: int = None, document_id: int = None,
                   target_date: datetime = None) -> int:
        """Create a new goal"""
        session = self.get_session()
        try:
            goal = Goal(
                goal_type=goal_type,
                target_value=target_value,
                topic_id=topic_id,
                document_id=document_id,
                target_date=target_date,
                original_target=target_value
            )
            
            # Calculate daily target if deadline goal
            if target_date and goal_type in ['pages', 'time']:
                days_available = (target_date - datetime.now()).days
                if days_available > 0:
                    goal.daily_target = target_value / days_available
            
            session.add(goal)
            session.commit()
            
            print(f"✅ Created {goal_type} goal: {target_value}")
            return goal.id
            
        except Exception as e:
            print(f"❌ Error creating goal: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def record_focus_session(self, topic_id: int = None, document_id: int = None,
                           start_time: datetime = None, end_time: datetime = None,
                           pages_read: int = 0, focus_level: str = "standard",
                           productivity_score: float = 0.0) -> int:
        """Record a focus session"""
        session = self.get_session()
        try:
            if not start_time:
                start_time = datetime.now()
            if not end_time:
                end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds() / 60  # minutes
            
            focus_session = FocusSession(
                topic_id=topic_id,
                document_id=document_id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                pages_read=pages_read,
                was_focus_mode=True,
                focus_level=focus_level,
                productivity_score=productivity_score
            )
            
            session.add(focus_session)
            session.commit()
            
            return focus_session.id
            
        except Exception as e:
            print(f"❌ Error recording focus session: {e}")
            session.rollback()
            return None
        finally:
            session.close()

# Initialize database manager
db_manager = DatabaseManager()

# Stage 5: Initialize with enhanced settings
def initialize_stage5_settings():
    """Initialize Stage 5 settings"""
    session = db_manager.get_session()
    try:
        stage5_settings = [
            # Existing settings
            ("default_session_duration", "25"),  # Pomodoro
            ("sprint_duration", "5"),  # Sprint minutes
            ("break_duration", "5"),  # Break minutes
            ("theme", "light"),
            ("auto_save_notes", "true"),
            
            # Stage 5: Enhanced settings
            ("default_focus_level", "standard"),
            ("auto_break_reminders", "true"),
            ("break_interval_minutes", "25"),
            ("productivity_tracking", "true"),
            ("adaptive_goal_adjustment", "true"),
            ("goal_reminder_notifications", "true"),
            ("auto_topic_suggestions", "true"),
            ("topic_color_coding", "true"),
            ("daily_goal_summary", "true"),
            ("focus_analytics_enabled", "true"),
            ("streak_tracking", "true"),
            ("minimum_streak_minutes", "10")
        ]
        
        for key, value in stage5_settings:
            existing = session.query(Settings).filter_by(key=key).first()
            if not existing:
                session.add(Settings(key=key, value=value))
        
        session.commit()
        print("✅ Stage 5 settings initialized")
        
    except Exception as e:
        print(f"❌ Error adding Stage 5 settings: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Create tables when run directly
    db_manager.create_tables()
    
    # Initialize settings including Stage 5
    initialize_stage5_settings()
    
    # Create default topic if none exists
    general_topic_id = db_manager.get_or_create_topic(
        "General", 
        "Default topic for uncategorized documents",
        "#7E22CE"
    )
    
    print("✅ Database initialized with Stage 5 enhancements")