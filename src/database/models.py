"""
SprintReader Database Models
SQLAlchemy ORM models for the application
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    Float, ForeignKey, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()

class Document(Base):
    """PDF documents being read"""
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
    
    # Relationships
    reading_sessions = relationship("ReadingSession", back_populates="document")
    notes = relationship("Note", back_populates="document")
    goals = relationship("Goal", back_populates="document")

class ReadingSession(Base):
    """Individual reading sessions"""
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
    
    # Relationships
    document = relationship("Document", back_populates="reading_sessions")

class Note(Base):
    """Notes and highlights from PDFs"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    page_number = Column(Integer, nullable=False)
    highlighted_text = Column(Text)
    note_content = Column(Text)
    topic = Column(String(255))
    x_position = Column(Float)  # for highlight positioning
    y_position = Column(Float)
    width = Column(Float)
    height = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="notes")

class Goal(Base):
    """Reading goals and progress tracking"""
    __tablename__ = 'goals'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    goal_type = Column(String(50))  # 'time', 'pages', 'completion'
    target_value = Column(Float)  # target minutes or pages
    current_value = Column(Float, default=0.0)
    target_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="goals")

class Settings(Base):
    """Application settings"""
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
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all tables (use with caution)"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️  All tables dropped")

# Initialize database manager
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Create tables when run directly
    db_manager.create_tables()
    
    # Add some default settings
    session = db_manager.get_session()
    try:
        # Check if settings exist
        existing_settings = session.query(Settings).first()
        if not existing_settings:
            default_settings = [
                Settings(key="default_session_duration", value="25"),  # Pomodoro
                Settings(key="sprint_duration", value="5"),  # Sprint minutes
                Settings(key="break_duration", value="5"),  # Break minutes
                Settings(key="theme", value="light"),
                Settings(key="auto_save_notes", value="true"),
            ]
            session.add_all(default_settings)
            session.commit()
            print("✅ Default settings added")
        else:
            print("⚠️  Settings already exist")
    except Exception as e:
        print(f"❌ Error adding default settings: {e}")
        session.rollback()
    finally:
        session.close()
