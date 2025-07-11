"""
SprintReader PDF Handler
Core PDF operations using PyMuPDF (fitz)
"""

import fitz  # PyMuPDF
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from database.models import db_manager, Document, ReadingSession

class PDFHandler:
    """Handles PDF operations and metadata"""
    
    def __init__(self):
        self.current_doc: Optional[fitz.Document] = None
        self.current_page: int = 0
        self.total_pages: int = 0
        self.document_id: Optional[int] = None
        self.session_start_time: Optional[datetime] = None
        self.page_start_time: Optional[datetime] = None
        self.page_times: Dict[int, float] = {}  # page_number -> seconds spent
        
    def open_pdf(self, filepath: str) -> bool:
        """Open a PDF file and initialize tracking"""
        try:
            # Close existing document if open
            if self.current_doc:
                self.close_pdf()
            
            # Open new document
            self.current_doc = fitz.open(filepath)
            self.total_pages = len(self.current_doc)
            
            # Get or create database entry
            self.document_id = self._get_or_create_document(filepath)
            
            # Load saved position
            self.current_page = self._get_saved_position()
            
            # Start session tracking
            self._start_session()
            
            print(f"✅ PDF opened: {os.path.basename(filepath)}")
            print(f"📄 Pages: {self.total_pages}")
            print(f"📍 Starting at page: {self.current_page + 1}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error opening PDF: {e}")
            return False
    
    def close_pdf(self):
        """Close current PDF and save progress"""
        if self.current_doc:
            # End current page timing
            if self.page_start_time:
                self._end_page_timing()
            
            # End session
            self._end_session()
            
            # Save progress
            self._save_progress()
            
            # Close document
            self.current_doc.close()
            self.current_doc = None
            self.document_id = None
            
            print("📚 PDF closed and progress saved")
    
    def get_page_pixmap(self, page_num: int, zoom: float = 1.0) -> Optional[fitz.Pixmap]:
        """Get page as pixmap for rendering"""
        if not self.current_doc or page_num >= self.total_pages:
            return None
        
        try:
            page = self.current_doc[page_num]
            mat = fitz.Matrix(zoom, zoom)  # Create zoom matrix
            pixmap = page.get_pixmap(matrix=mat)
            return pixmap
        except Exception as e:
            print(f"❌ Error rendering page {page_num}: {e}")
            return None
    
    def go_to_page(self, page_num: int) -> bool:
        """Navigate to specific page"""
        if not self.current_doc or page_num < 0 or page_num >= self.total_pages:
            return False
        
        # End timing for current page
        if self.page_start_time:
            self._end_page_timing()
        
        # Update current page
        old_page = self.current_page
        self.current_page = page_num
        
        # Start timing for new page
        self._start_page_timing()
        
        print(f"📖 Navigated from page {old_page + 1} to {self.current_page + 1}")
        return True
    
    def next_page(self) -> bool:
        """Go to next page"""
        return self.go_to_page(self.current_page + 1)
    
    def previous_page(self) -> bool:
        """Go to previous page"""
        return self.go_to_page(self.current_page - 1)
    
    def get_document_info(self) -> Dict:
        """Get current document information"""
        if not self.current_doc:
            return {}
        
        metadata = self.current_doc.metadata
        
        return {
            'title': metadata.get('title', 'Unknown'),
            'author': metadata.get('author', 'Unknown'),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'created': metadata.get('creationDate', ''),
            'modified': metadata.get('modDate', ''),
            'total_pages': self.total_pages,
            'current_page': self.current_page + 1,
            'progress_percent': round((self.current_page / self.total_pages) * 100, 1) if self.total_pages > 0 else 0
        }
    
    def get_reading_stats(self) -> Dict:
        """Get current reading session statistics"""
        if not self.session_start_time:
            return {}
        
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60  # minutes
        pages_read = len(self.page_times)
        
        reading_speed = 0
        if session_duration > 0 and pages_read > 0:
            reading_speed = pages_read / session_duration  # pages per minute
        
        return {
            'session_duration': round(session_duration, 1),
            'pages_read_this_session': pages_read,
            'reading_speed': round(reading_speed, 2),
            'current_page_time': self._get_current_page_time(),
            'total_page_times': sum(self.page_times.values())
        }
    
    def search_text(self, query: str, page_num: Optional[int] = None) -> List[Dict]:
        """Search for text in PDF"""
        if not self.current_doc:
            return []
        
        results = []
        pages_to_search = [page_num] if page_num is not None else range(self.total_pages)
        
        for page_idx in pages_to_search:
            try:
                page = self.current_doc[page_idx]
                text_instances = page.search_for(query)
                
                for inst in text_instances:
                    results.append({
                        'page': page_idx + 1,
                        'bbox': inst,
                        'text': query
                    })
            except Exception as e:
                print(f"❌ Error searching page {page_idx}: {e}")
        
        return results
    
    def extract_page_text(self, page_num: int) -> str:
        """Extract text from specific page"""
        if not self.current_doc or page_num >= self.total_pages:
            return ""
        
        try:
            page = self.current_doc[page_num]
            return page.get_text()
        except Exception as e:
            print(f"❌ Error extracting text from page {page_num}: {e}")
            return ""
    
    def _get_or_create_document(self, filepath: str) -> int:
        """Get existing document or create new one in database"""
        session = db_manager.get_session()
        try:
            filename = os.path.basename(filepath)
            
            # Try to find existing document
            doc = session.query(Document).filter_by(filepath=filepath).first()
            
            if not doc:
                # Create new document
                info = self.get_document_info()
                doc = Document(
                    filename=filename,
                    filepath=filepath,
                    title=info.get('title', filename),
                    total_pages=self.total_pages,
                    current_page=1
                )
                session.add(doc)
                session.commit()
                print(f"📝 New document created in database: {filename}")
            else:
                print(f"📖 Existing document loaded: {filename}")
            
            return doc.id
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def _get_saved_position(self) -> int:
        """Get saved reading position from database"""
        if not self.document_id:
            return 0
        
        session = db_manager.get_session()
        try:
            doc = session.query(Document).filter_by(id=self.document_id).first()
            if doc and doc.current_page:
                return doc.current_page - 1  # Convert to 0-based indexing
            return 0
        except Exception as e:
            print(f"❌ Error loading saved position: {e}")
            return 0
        finally:
            session.close()
    
    def _save_progress(self):
        """Save reading progress to database"""
        if not self.document_id:
            return
        
        session = db_manager.get_session()
        try:
            doc = session.query(Document).filter_by(id=self.document_id).first()
            if doc:
                doc.current_page = self.current_page + 1  # Convert to 1-based
                doc.updated_at = datetime.utcnow()
                
                # Update reading stats if we have them
                stats = self.get_reading_stats()
                if stats.get('reading_speed', 0) > 0:
                    doc.reading_speed = stats['reading_speed']
                
                session.commit()
                print(f"💾 Progress saved: Page {self.current_page + 1}")
        except Exception as e:
            print(f"❌ Error saving progress: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _start_session(self):
        """Start a new reading session"""
        self.session_start_time = datetime.now()
        self.page_times = {}
        self._start_page_timing()
        print(f"⏰ Reading session started at {self.session_start_time.strftime('%H:%M:%S')}")
    
    def _end_session(self):
        """End current reading session and save to database"""
        if not self.session_start_time or not self.document_id:
            return
        
        # Calculate session stats
        end_time = datetime.now()
        duration = (end_time - self.session_start_time).total_seconds() / 60  # minutes
        pages_read = len(self.page_times)
        
        # Save session to database
        session = db_manager.get_session()
        try:
            reading_session = ReadingSession(
                document_id=self.document_id,
                start_time=self.session_start_time,
                end_time=end_time,
                duration=duration,
                pages_read=pages_read,
                start_page=self.current_page + 1,  # 1-based
                end_page=self.current_page + 1,
                session_type='regular'
            )
            session.add(reading_session)
            session.commit()
            
            print(f"📊 Session saved: {duration:.1f} min, {pages_read} pages")
            
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            session.rollback()
        finally:
            session.close()
        
        self.session_start_time = None
    
    def _start_page_timing(self):
        """Start timing current page"""
        self.page_start_time = datetime.now()
    
    def _end_page_timing(self):
        """End timing for current page and record time"""
        if self.page_start_time:
            page_duration = (datetime.now() - self.page_start_time).total_seconds()
            self.page_times[self.current_page] = page_duration
            print(f"⏱️  Page {self.current_page + 1} read in {page_duration:.1f}s")
            self.page_start_time = None
    
    def _get_current_page_time(self) -> float:
        """Get time spent on current page so far"""
        if self.page_start_time:
            return (datetime.now() - self.page_start_time).total_seconds()
        return 0.0