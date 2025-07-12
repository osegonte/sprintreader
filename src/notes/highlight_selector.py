"""
Highlight Selector - Interactive PDF text selection and highlighting
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QComboBox, QLineEdit, QDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap, QMouseEvent
from typing import List, Tuple, Optional
import fitz  # PyMuPDF

class TextSelection:
    """Represents a text selection on a PDF page"""
    
    def __init__(self, page_num: int, rect: QRect, text: str):
        self.page_num = page_num
        self.rect = rect  # Selection rectangle
        self.text = text  # Selected text
        self.color = QColor(255, 255, 0, 100)  # Yellow highlight with transparency

class HighlightableLabel(QLabel):
    """PDF display label that supports text selection and highlighting"""
    
    text_selected = pyqtSignal(str, QRect)  # text, selection_rect
    highlight_requested = pyqtSignal(str, QRect)  # text, position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # Selection state
        self.selecting = False
        self.selection_start = QPoint()
        self.selection_end = QPoint()
        self.current_selection = QRect()
        
        # PDF text data (from PyMuPDF)
        self.text_blocks = []  # List of text blocks from PDF
        self.page_number = 0
        self.zoom_factor = 1.0
        
        # Highlights
        self.highlights = []  # List of TextSelection objects
        
        # Styling
        self.selection_color = QColor(0, 120, 215, 100)  # Blue selection
        self.highlight_color = QColor(255, 255, 0, 100)  # Yellow highlight
    
    def set_pdf_page_data(self, page_number: int, text_blocks: List, zoom_factor: float = 1.0):
        """Set PDF page text data for selection"""
        self.page_number = page_number
        self.text_blocks = text_blocks
        self.zoom_factor = zoom_factor
        self.update()
    
    def add_highlight(self, text: str, rect: QRect):
        """Add a highlight to the page"""
        highlight = TextSelection(self.page_number, rect, text)
        self.highlights.append(highlight)
        self.update()
    
    def clear_highlights(self):
        """Clear all highlights from the page"""
        self.highlights.clear()
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start text selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = True
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.current_selection = QRect()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Update selection during drag"""
        if self.selecting:
            self.selection_end = event.pos()
            self.current_selection = QRect(self.selection_start, self.selection_end).normalized()
            self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Complete text selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            
            if self.current_selection.width() > 10 and self.current_selection.height() > 10:
                # Extract text from selection
                selected_text = self._extract_text_from_selection(self.current_selection)
                
                if selected_text.strip():
                    self.text_selected.emit(selected_text, self.current_selection)
                    # Show highlight option
                    self._show_highlight_tooltip(event.pos(), selected_text)
            
            self.current_selection = QRect()
            self.update()
        
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        """Custom paint to show selection and highlights"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw existing highlights
        for highlight in self.highlights:
            painter.fillRect(highlight.rect, highlight.color)
            
            # Draw highlight border
            pen = QPen(QColor(200, 200, 0), 2)
            painter.setPen(pen)
            painter.drawRect(highlight.rect)
        
        # Draw current selection
        if self.selecting and not self.current_selection.isEmpty():
            painter.fillRect(self.current_selection, self.selection_color)
            
            pen = QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.current_selection)
    
    def _extract_text_from_selection(self, selection_rect: QRect) -> str:
        """Extract text from the selection rectangle using PDF text blocks"""
        if not self.text_blocks:
            return ""
        
        selected_text = ""
        
        # Convert selection rect to PDF coordinates
        pdf_rect = self._qt_rect_to_pdf_rect(selection_rect)
        
        # Find intersecting text blocks
        for block in self.text_blocks:
            if self._rects_intersect(pdf_rect, block.get('bbox', [0, 0, 0, 0])):
                # Check individual lines and characters
                for line in block.get('lines', []):
                    line_bbox = line.get('bbox', [0, 0, 0, 0])
                    if self._rects_intersect(pdf_rect, line_bbox):
                        # Add line text
                        for span in line.get('spans', []):
                            span_bbox = span.get('bbox', [0, 0, 0, 0])
                            if self._rects_intersect(pdf_rect, span_bbox):
                                selected_text += span.get('text', '') + " "
        
        return selected_text.strip()
    
    def _qt_rect_to_pdf_rect(self, qt_rect: QRect) -> List[float]:
        """Convert Qt rectangle to PDF coordinates"""
        # Adjust for zoom and coordinate system differences
        x0 = qt_rect.left() / self.zoom_factor
        y0 = qt_rect.top() / self.zoom_factor
        x1 = qt_rect.right() / self.zoom_factor
        y1 = qt_rect.bottom() / self.zoom_factor
        
        return [x0, y0, x1, y1]
    
    def _rects_intersect(self, rect1: List[float], rect2: List[float]) -> bool:
        """Check if two rectangles intersect"""
        x0_1, y0_1, x1_1, y1_1 = rect1
        x0_2, y0_2, x1_2, y1_2 = rect2
        
        return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)
    
    def _show_highlight_tooltip(self, position: QPoint, text: str):
        """Show tooltip for adding highlight"""
        # Emit signal for parent to handle
        self.highlight_requested.emit(text, QRect(position, position))

class HighlightDialog(QDialog):
    """Dialog for creating notes from highlights"""
    
    note_created = pyqtSignal(str, str, str, str)  # topic, title, content, highlighted_text
    
    def __init__(self, highlighted_text: str, page_number: int, parent=None):
        super().__init__(parent)
        self.highlighted_text = highlighted_text
        self.page_number = page_number
        self.setModal(True)
        self.setWindowTitle("Add Note from Highlight")
        self.resize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("✍️ Create Note from Highlight")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Highlighted text display
        highlight_group = QWidget()
        highlight_layout = QVBoxLayout(highlight_group)
        
        highlight_layout.addWidget(QLabel("📄 Highlighted Text:"))
        
        self.highlight_display = QTextEdit()
        self.highlight_display.setPlainText(self.highlighted_text)
        self.highlight_display.setMaximumHeight(80)
        self.highlight_display.setReadOnly(True)
        self.highlight_display.setStyleSheet("""
            QTextEdit {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        highlight_layout.addWidget(self.highlight_display)
        
        page_info = QLabel(f"📍 Page {self.page_number}")
        page_info.setStyleSheet("color: #666; font-style: italic;")
        highlight_layout.addWidget(page_info)
        
        layout.addWidget(highlight_group)
        
        # Topic selection
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("🗂️ Topic:"))
        
        self.topic_combo = QComboBox()
        self.topic_combo.setEditable(True)
        self.topic_combo.addItems([
            "General", "Research", "Study Notes", "Important Concepts",
            "Questions", "Summary", "Quotes", "Action Items"
        ])
        topic_layout.addWidget(self.topic_combo)
        
        layout.addLayout(topic_layout)
        
        # Note title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("📝 Title:"))
        
        self.title_input = QLineEdit()
        # Auto-generate title from highlight
        auto_title = self._generate_title_from_highlight()
        self.title_input.setText(auto_title)
        title_layout.addWidget(self.title_input)
        
        layout.addLayout(title_layout)
        
        # Note content
        layout.addWidget(QLabel("✍️ Your Notes:"))
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText(
            "Add your thoughts, analysis, or questions about this highlight...\n\n"
            "💡 Tips:\n"
            "• Use [[Note Name]] to link to other notes\n"
            "• Add #tags for organization\n"
            "• Write key insights or connections"
        )
        self.content_input.setMinimumHeight(150)
        layout.addWidget(self.content_input)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("🏷️ Tags:"))
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("concept, important, review (comma-separated)")
        tags_layout.addWidget(self.tags_input)
        
        layout.addLayout(tags_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 Save Note")
        save_btn.clicked.connect(self.save_note)
        save_btn.setDefault(True)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #7E22CE;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B21A8;
            }
        """)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Focus on content input
        self.content_input.setFocus()
    
    def _generate_title_from_highlight(self) -> str:
        """Generate a note title from the highlighted text"""
        # Take first 6 words or 40 characters, whichever is shorter
        words = self.highlighted_text.split()
        if len(words) <= 6:
            return ' '.join(words)
        else:
            title = ' '.join(words[:6])
            if len(title) > 40:
                return title[:37] + "..."
            return title + "..."
    
    def save_note(self):
        """Save the note and close dialog"""
        topic = self.topic_combo.currentText().strip()
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        if not topic:
            topic = "General"
        
        if not title:
            title = self._generate_title_from_highlight()
        
        # Process tags
        tags_text = self.tags_input.text().strip()
        if tags_text:
            # Add tags to content for processing
            content += f"\n\nTags: {tags_text}"
        
        self.note_created.emit(topic, title, content, self.highlighted_text)
        self.accept()

class NotesPanel(QWidget):
    """Side panel for displaying and managing notes"""
    
    note_selected = pyqtSignal(str)  # note_id
    note_edit_requested = pyqtSignal(str)  # note_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_notes = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the notes panel UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📝 Notes")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Filter/search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search notes...")
        self.search_input.textChanged.connect(self.filter_notes)
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)
        
        # Topic filter
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("Topic:"))
        
        self.topic_filter = QComboBox()
        self.topic_filter.addItem("All Topics")
        self.topic_filter.currentTextChanged.connect(self.filter_notes)
        topic_layout.addWidget(self.topic_filter)
        
        layout.addLayout(topic_layout)
        
        # Notes list
        self.notes_scroll = QScrollArea()
        self.notes_scroll.setWidgetResizable(True)
        self.notes_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.notes_container = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_container)
        self.notes_layout.addStretch()
        
        self.notes_scroll.setWidget(self.notes_container)
        layout.addWidget(self.notes_scroll)
        
        # Add note button
        add_note_btn = QPushButton("➕ Add Manual Note")
        add_note_btn.clicked.connect(self.add_manual_note)
        layout.addWidget(add_note_btn)
    
    def update_notes_list(self, notes: List, topics: dict):
        """Update the notes list display"""
        # Clear existing notes
        for i in reversed(range(self.notes_layout.count() - 1)):  # Keep stretch
            child = self.notes_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.current_notes = notes
        
        # Update topic filter
        self.topic_filter.clear()
        self.topic_filter.addItem("All Topics")
        for topic in topics.values():
            self.topic_filter.addItem(topic.name)
        
        # Add note widgets
        for note in notes:
            note_widget = self.create_note_widget(note, topics)
            self.notes_layout.insertWidget(self.notes_layout.count() - 1, note_widget)
    
    def create_note_widget(self, note, topics: dict) -> QWidget:
        """Create a widget for displaying a note"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 2px;
            }
            QWidget:hover {
                background-color: #e9ecef;
                border-color: #7E22CE;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header with title and topic
        header_layout = QHBoxLayout()
        
        title_label = QLabel(note.title)
        title_label.setWordWrap(True)
        font = QFont()
        font.setBold(True)
        title_label.setFont(font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Topic badge
        topic_name = topics.get(note.topic_id, type('obj', (object,), {'name': 'Unknown'})).name
        topic_badge = QLabel(f"🗂️ {topic_name}")
        topic_badge.setStyleSheet("""
            QLabel {
                background-color: #7E22CE;
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 10px;
            }
        """)
        header_layout.addWidget(topic_badge)
        
        layout.addLayout(header_layout)
        
        # Excerpt (if available)
        if note.excerpt:
            excerpt_label = QLabel(f"📄 \"{note.excerpt[:100]}...\"" if len(note.excerpt) > 100 else f"📄 \"{note.excerpt}\"")
            excerpt_label.setWordWrap(True)
            excerpt_label.setStyleSheet("color: #6c757d; font-style: italic; margin: 4px 0;")
            layout.addWidget(excerpt_label)
        
        # Content preview
        if note.content:
            content_preview = note.content[:150] + "..." if len(note.content) > 150 else note.content
            content_label = QLabel(content_preview)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("margin: 4px 0;")
            layout.addWidget(content_label)
        
        # Footer with metadata
        footer_layout = QHBoxLayout()
        
        # Page info
        page_label = QLabel(f"📍 Page {note.page_number}")
        page_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        footer_layout.addWidget(page_label)
        
        footer_layout.addStretch()
        
        # Date
        date_label = QLabel(note.created_at[:10])
        date_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        footer_layout.addWidget(date_label)
        
        # Edit button
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(24, 24)
        edit_btn.clicked.connect(lambda: self.note_edit_requested.emit(note.id))
        footer_layout.addWidget(edit_btn)
        
        layout.addLayout(footer_layout)
        
        # Tags
        if note.tags:
            tags_layout = QHBoxLayout()
            for tag in note.tags[:3]:  # Show max 3 tags
                tag_label = QLabel(f"#{tag}")
                tag_label.setStyleSheet("""
                    QLabel {
                        background-color: #e3f2fd;
                        color: #1976d2;
                        border-radius: 8px;
                        padding: 1px 6px;
                        font-size: 10px;
                    }
                """)
                tags_layout.addWidget(tag_label)
            
            if len(note.tags) > 3:
                more_label = QLabel(f"+{len(note.tags) - 3}")
                more_label.setStyleSheet("color: #6c757d; font-size: 10px;")
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
        # Make widget clickable
        widget.mousePressEvent = lambda event: self.note_selected.emit(note.id)
        
        return widget
    
    def filter_notes(self):
        """Filter notes based on search and topic"""
        search_text = self.search_input.text().lower()
        topic_filter = self.topic_filter.currentText()
        
        for i in range(self.notes_layout.count() - 1):  # Exclude stretch
            widget = self.notes_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'note'):
                note = widget.note
                
                # Check search filter
                search_match = (
                    search_text in note.title.lower() or
                    search_text in note.content.lower() or
                    search_text in note.excerpt.lower() or
                    any(search_text in tag.lower() for tag in note.tags)
                )
                
                # Check topic filter
                topic_match = (
                    topic_filter == "All Topics" or
                    topic_filter == note.topic_id  # This would need topic name lookup
                )
                
                widget.setVisible(search_match and topic_match)
    
    def add_manual_note(self):
        """Open dialog to add a manual note (not from highlight)"""
        dialog = HighlightDialog("", 1, self)  # Empty highlight for manual note
        dialog.setWindowTitle("Add Manual Note")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Handle manual note creation
            pass