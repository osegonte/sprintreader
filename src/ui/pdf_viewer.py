"""
SprintReader Stage 4 PDF Viewer Widget - SYNTAX FIXED
Enhanced with note-taking, highlighting, and WORKING time estimation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QSpinBox, QFileDialog, QSplitter, QTextEdit, 
    QGroupBox, QProgressBar, QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import fitz  # PyMuPDF
import os
from typing import Optional, List
from datetime import datetime
from pdf_handler.pdf_handler import PDFHandler
from notes.note_manager import NoteManager
from notes.highlight_selector import HighlightableLabel, HighlightDialog, NotesPanel

class PDFViewerWidget(QWidget):
    """Enhanced PDF viewer widget with note-taking and WORKING time estimation"""
    
    # Signals
    page_changed = pyqtSignal(int)
    document_opened = pyqtSignal(str)
    note_created = pyqtSignal(str)  # note_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_handler = PDFHandler()
        self.note_manager = NoteManager()
        
        # Display settings
        self.zoom_level = 1.0
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self.current_zoom_index = 2  # Start at 1.0x
        
        # Current document notes
        self.current_document_notes = []
        self.current_page_highlights = []
        
        # Time estimation tracking - ENHANCED
        self.time_estimator = None
        self.reading_predictor = None
        self.last_estimation_update = None
        self.current_estimation = {}
        
        # Timers
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._autosave_progress)
        self.autosave_timer.start(30000)  # Auto-save every 30 seconds
        
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats_display)
        self.stats_timer.start(1000)  # Update every second
        
        # Time estimation update timer - NEW
        self.estimation_timer = QTimer()
        self.estimation_timer.timeout.connect(self._update_time_estimation)
        self.estimation_timer.start(10000)  # Update estimates every 10 seconds
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the user interface with note-taking features"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create toolbar
        self.create_toolbar(main_layout)
        
        # Create main splitter (3 panels)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left sidebar - Document info and stats
        self.create_sidebar(main_splitter)
        
        # Center - PDF display with highlighting
        self.create_pdf_display(main_splitter)
        
        # Right sidebar - Notes panel
        self.create_notes_panel(main_splitter)
        
        # Set splitter proportions (sidebar: 20%, PDF: 50%, notes: 30%)
        main_splitter.setSizes([300, 700, 400])
        
        # Status bar
        self.create_status_bar(main_layout)
        
        # Initially disable navigation controls
        self._update_navigation_state()
    
    def create_toolbar(self, parent_layout):
        """Create the main toolbar with note-taking options"""
        toolbar_layout = QHBoxLayout()
        
        # File operations
        self.open_btn = QPushButton("📁 Open PDF")
        self.open_btn.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.open_btn)
        
        toolbar_layout.addWidget(QLabel(" | "))
        
        # Navigation controls
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_page)
        toolbar_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("▶ Next")
        self.next_btn.clicked.connect(self.next_page)
        toolbar_layout.addWidget(self.next_btn)
        
        # Page input
        toolbar_layout.addWidget(QLabel("Page:"))
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        toolbar_layout.addWidget(self.page_spinbox)
        
        self.page_total_label = QLabel("/ 0")
        toolbar_layout.addWidget(self.page_total_label)
        
        toolbar_layout.addWidget(QLabel(" | "))
        
        # Zoom controls
        self.zoom_out_btn = QPushButton("🔍➖")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar_layout.addWidget(self.zoom_label)
        
        self.zoom_in_btn = QPushButton("🔍➕")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(self.zoom_in_btn)
        
        toolbar_layout.addWidget(QLabel(" | "))
        
        # Note-taking controls
        self.highlight_mode_btn = QPushButton("🖍️ Highlight Mode")
        self.highlight_mode_btn.setCheckable(True)
        self.highlight_mode_btn.toggled.connect(self.toggle_highlight_mode)
        toolbar_layout.addWidget(self.highlight_mode_btn)
        
        self.add_note_btn = QPushButton("📝 Quick Note")
        self.add_note_btn.clicked.connect(self.add_quick_note)
        toolbar_layout.addWidget(self.add_note_btn)
        
        # Stretch to push remaining items to the right
        toolbar_layout.addStretch()
        
        # Notes summary
        self.notes_summary_label = QLabel("📝 0 notes")
        toolbar_layout.addWidget(self.notes_summary_label)
        
        # Session info
        self.session_label = QLabel("📚 No Document")
        toolbar_layout.addWidget(self.session_label)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_sidebar(self, splitter):
        """Create the left sidebar with document info and stats"""
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # Create tab widget for better organization
        sidebar_tabs = QTabWidget()
        
        # Document Info Tab
        doc_tab = QWidget()
        doc_layout = QVBoxLayout(doc_tab)
        
        self.doc_title_label = QLabel("No document loaded")
        self.doc_title_label.setWordWrap(True)
        font = QFont()
        font.setBold(True)
        self.doc_title_label.setFont(font)
        doc_layout.addWidget(self.doc_title_label)
        
        self.doc_details_text = QTextEdit()
        self.doc_details_text.setMaximumHeight(120)
        self.doc_details_text.setReadOnly(True)
        doc_layout.addWidget(self.doc_details_text)
        
        # Reading Progress
        progress_group = QGroupBox("📊 Reading Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_details = QTextEdit()
        self.progress_details.setMaximumHeight(80)
        self.progress_details.setReadOnly(True)
        progress_layout.addWidget(self.progress_details)
        
        doc_layout.addWidget(progress_group)
        
        # Time Estimation Group - ENHANCED
        estimation_group = QGroupBox("⏱️ Smart Time Estimation")
        estimation_layout = QVBoxLayout(estimation_group)
        
        self.estimation_display = QTextEdit()
        self.estimation_display.setMaximumHeight(120)
        self.estimation_display.setReadOnly(True)
        self.estimation_display.setStyleSheet("""
            QTextEdit {
                background-color: #f0f8ff;
                border: 1px solid #4169e1;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        estimation_layout.addWidget(self.estimation_display)
        
        doc_layout.addWidget(estimation_group)
        doc_layout.addStretch()
        
        sidebar_tabs.addTab(doc_tab, "📄 Document")
        
        # Stats Tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_group = QGroupBox("⏱️ Session Stats")
        stats_group_layout = QVBoxLayout(stats_group)
        
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        stats_group_layout.addWidget(self.stats_display)
        
        stats_layout.addWidget(stats_group)
        
        # Note-taking stats
        notes_stats_group = QGroupBox("📝 Note Stats")
        notes_stats_layout = QVBoxLayout(notes_stats_group)
        
        self.notes_stats_display = QTextEdit()
        self.notes_stats_display.setMaximumHeight(100)
        self.notes_stats_display.setReadOnly(True)
        notes_stats_layout.addWidget(self.notes_stats_display)
        
        stats_layout.addWidget(notes_stats_group)
        stats_layout.addStretch()
        
        sidebar_tabs.addTab(stats_tab, "📊 Stats")
        
        sidebar_layout.addWidget(sidebar_tabs)
        splitter.addWidget(sidebar_widget)
    
    def create_pdf_display(self, splitter):
        """Create the main PDF display area with highlighting support"""
        pdf_widget = QWidget()
        pdf_layout = QVBoxLayout(pdf_widget)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        
        # Highlighting toolbar
        highlight_toolbar = QHBoxLayout()
        
        self.clear_highlights_btn = QPushButton("🗑️ Clear Highlights")
        self.clear_highlights_btn.clicked.connect(self.clear_page_highlights)
        self.clear_highlights_btn.setEnabled(False)
        highlight_toolbar.addWidget(self.clear_highlights_btn)
        
        highlight_toolbar.addStretch()
        
        self.highlight_status_label = QLabel("Select text to create notes")
        highlight_status_label_style = "color: #666; font-style: italic; padding: 4px;"
        self.highlight_status_label.setStyleSheet(highlight_status_label_style)
        highlight_toolbar.addWidget(self.highlight_status_label)
        
        pdf_layout.addLayout(highlight_toolbar)
        
        # Create scroll area for PDF with highlighting
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Use highlightable PDF label
        self.pdf_label = HighlightableLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                margin: 10px;
            }
        """)
        self.pdf_label.setText("📖 Open a PDF file to start reading and taking notes")
        self.pdf_label.setMinimumSize(400, 600)
        
        self.scroll_area.setWidget(self.pdf_label)
        pdf_layout.addWidget(self.scroll_area)
        
        splitter.addWidget(pdf_widget)
    
    def create_notes_panel(self, splitter):
        """Create the right sidebar notes panel"""
        self.notes_panel = NotesPanel()
        splitter.addWidget(self.notes_panel)
    
    def create_status_bar(self, parent_layout):
        """Create the status bar"""
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready to load PDF")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Time estimation status - NEW
        self.estimation_status_label = QLabel("⏱️ No estimation")
        self.estimation_status_label.setStyleSheet("color: #4169e1; font-weight: bold;")
        status_layout.addWidget(self.estimation_status_label)
        
        status_layout.addWidget(QLabel(" | "))
        
        # Note mode indicator
        self.note_mode_label = QLabel("📝 Notes: Ready")
        status_layout.addWidget(self.note_mode_label)
        
        self.reading_time_label = QLabel("⏰ 0:00")
        status_layout.addWidget(self.reading_time_label)
        
        parent_layout.addLayout(status_layout)
    
    def connect_signals(self):
        """Connect signals for note-taking functionality"""
        # PDF highlighting signals
        self.pdf_label.text_selected.connect(self.on_text_selected)
        self.pdf_label.highlight_requested.connect(self.on_highlight_requested)
        
        # Notes panel signals
        self.notes_panel.note_selected.connect(self.on_note_selected)
        self.notes_panel.note_edit_requested.connect(self.on_note_edit_requested)
        
        # Note manager signals
        self.note_manager.note_created.connect(self.on_note_created)
        self.note_manager.note_updated.connect(self.on_note_updated)
    
    def open_file(self):
        """Open file dialog and load PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            self.load_pdf(file_path)
    
    def load_pdf(self, file_path: str):
        """Load a PDF file and initialize note-taking"""
        if self.pdf_handler.open_pdf(file_path):
            # Initialize time estimation - ENHANCED
            self._initialize_time_estimation()
            
            # Update UI
            self._update_document_info()
            self._update_navigation_state()
            self._render_current_page()
            
            # Load notes for this document
            self._load_document_notes()
            
            # Initial time estimation
            self._update_time_estimation()
            
            # Emit signal
            self.document_opened.emit(file_path)
            
            # Update status
            filename = os.path.basename(file_path)
            self.status_label.setText(f"Loaded: {filename}")
            self.session_label.setText(f"📚 {filename}")
            self.note_mode_label.setText("📝 Notes: Active")
            
            print(f"✅ PDF loaded with time estimation: {filename}")
        else:
            self.status_label.setText("❌ Failed to load PDF")
    
    def _initialize_time_estimation(self):
        """Initialize time estimation system - NEW"""
        try:
            from estimation.time_estimator import TimeEstimator
            from estimation.reading_predictor import ReadingPredictor
            
            self.time_estimator = TimeEstimator()
            self.reading_predictor = ReadingPredictor()
            
            print("✅ Time estimation system initialized")
        except Exception as e:
            print(f"❌ Error initializing time estimation: {e}")
            self.time_estimator = None
            self.reading_predictor = None
    
    def _update_time_estimation(self):
        """Update time estimation display - NEW"""
        if not self.pdf_handler.document_id or not self.time_estimator:
            self.estimation_display.setText("No document loaded or estimation unavailable")
            self.estimation_status_label.setText("⏱️ No estimation")
            return
        
        try:
            # Get document completion estimate
            estimate = self.time_estimator.estimate_document_completion(
                self.pdf_handler.document_id
            )
            
            if estimate:
                self.current_estimation = estimate
                
                # Format estimation display
                estimation_text = f"""
📖 Document: {estimate.get('document_title', 'Unknown')[:30]}...

📊 Progress:
• Current: Page {estimate.get('current_page', 0)} / {estimate.get('total_pages', 0)}
• Complete: {estimate.get('progress_percent', 0):.1f}%
• Remaining: {estimate.get('remaining_pages', 0)} pages

⏱️ Time Estimates:
• Per page: {estimate.get('avg_time_per_page_seconds', 0):.1f}s
• To finish: {estimate.get('estimated_time_remaining_formatted', 'Unknown')}
• Confidence: {estimate.get('confidence_level', 'Unknown')}

📅 Completion:
• At current pace: {self._format_completion_date(estimate.get('estimated_completion_date'))}

💡 Tip: {estimate.get('recommendation', 'Keep reading!')}
                """.strip()
                
                self.estimation_display.setText(estimation_text)
                
                # Update status bar
                remaining_time = estimate.get('estimated_time_remaining_formatted', 'Unknown')
                confidence = estimate.get('confidence_level', 'Unknown')
                self.estimation_status_label.setText(f"⏱️ {remaining_time} left ({confidence} confidence)")
                
                self.last_estimation_update = datetime.now()
                print(f"📊 Time estimation updated: {remaining_time} remaining")
            else:
                self.estimation_display.setText("⏱️ Building estimate...\nRead a few more pages for accurate predictions.")
                self.estimation_status_label.setText("⏱️ Building estimate...")
                
        except Exception as e:
            print(f"❌ Error updating time estimation: {e}")
            self.estimation_display.setText("⚠️ Estimation temporarily unavailable")
            self.estimation_status_label.setText("⏱️ Estimation error")
    
    def _format_completion_date(self, date_str: str) -> str:
        """Format completion date for display"""
        if not date_str:
            return "Unknown"
        try:
            # Extract just the date part
            return date_str[:10]  # YYYY-MM-DD format
        except:
            return "Unknown"
    
    def previous_page(self):
        """Go to previous page"""
        if self.pdf_handler.previous_page():
            self._render_current_page()
            self._update_ui_state()
            self._load_page_highlights()
            self._trigger_estimation_update()
    
    def next_page(self):
        """Go to next page"""
        if self.pdf_handler.next_page():
            self._render_current_page()
            self._update_ui_state()
            self._load_page_highlights()
            self._trigger_estimation_update()
    
    def go_to_page(self, page_num: int):
        """Go to specific page (1-based)"""
        if self.pdf_handler.go_to_page(page_num - 1):  # Convert to 0-based
            self._render_current_page()
            self._update_ui_state()
            self._load_page_highlights()
            self._trigger_estimation_update()
    
    def _trigger_estimation_update(self):
        """Trigger immediate estimation update after page change"""
        if self.time_estimator and self.pdf_handler.document_id:
            # Use QTimer.singleShot to update estimation after a short delay
            QTimer.singleShot(1000, self._update_time_estimation)
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            self.zoom_level = self.zoom_levels[self.current_zoom_index]
            self._render_current_page()
            self._update_zoom_display()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            self.zoom_level = self.zoom_levels[self.current_zoom_index]
            self._render_current_page()
            self._update_zoom_display()
    
    def toggle_highlight_mode(self, enabled: bool):
        """Toggle highlight selection mode"""
        if enabled:
            self.highlight_status_label.setText("🖍️ Highlight mode active - select text to create notes")
            self.pdf_label.setStyleSheet("""
                QLabel {
                    background-color: #fffacd;
                    border: 2px solid #ffd700;
                    margin: 10px;
                }
            """)
        else:
            self.highlight_status_label.setText("Select text to create notes")
            self.pdf_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 1px solid #ccc;
                    margin: 10px;
                }
            """)
    
    def add_quick_note(self):
        """Add a quick note without highlighting"""
        if not self.pdf_handler.document_id:
            QMessageBox.warning(self, "No Document", "Please open a PDF document first.")
            return
        
        dialog = HighlightDialog("", self.pdf_handler.current_page + 1, self)
        dialog.setWindowTitle("Add Quick Note")
        if dialog.exec() == dialog.DialogCode.Accepted:
            pass  # Note creation handled by signal
    
    def clear_page_highlights(self):
        """Clear all highlights from current page"""
        self.pdf_label.clear_highlights()
        self.clear_highlights_btn.setEnabled(False)
        self.highlight_status_label.setText("Highlights cleared")
    
    def on_text_selected(self, text: str, rect):
        """Handle text selection in PDF"""
        if len(text.strip()) < 5:  # Ignore very short selections
            return
        
        self.highlight_status_label.setText(f"Selected: {text[:30]}...")
    
    def on_highlight_requested(self, text: str, position):
        """Handle highlight creation request"""
        if not self.pdf_handler.document_id:
            return
        
        dialog = HighlightDialog(text, self.pdf_handler.current_page + 1, self)
        dialog.note_created.connect(self.create_note_from_highlight)
        dialog.exec()
    
    def create_note_from_highlight(self, topic: str, title: str, content: str, highlighted_text: str):
        """Create note from highlight dialog"""
        if not self.pdf_handler.document_id:
            return
        
        # Create note using note manager
        note_id = self.note_manager.create_note_from_highlight(
            document_id=self.pdf_handler.document_id,
            page_number=self.pdf_handler.current_page + 1,
            highlighted_text=highlighted_text,
            topic_name=topic,
            user_notes=content,
            position=(0, 0)  # Position from PDF coordinates
        )
        
        # Add visual highlight to PDF
        if highlighted_text:
            # This would need proper coordinates from the text selection
            highlight_rect = self.pdf_label.current_selection
            self.pdf_label.add_highlight(highlighted_text, highlight_rect)
            self.clear_highlights_btn.setEnabled(True)
        
        # Update notes display
        self._load_document_notes()
        self._update_notes_stats()
        
        self.highlight_status_label.setText(f"✅ Note created: {title}")
        
        # Emit signal
        self.note_created.emit(note_id)
    
    def on_note_selected(self, note_id: str):
        """Handle note selection in notes panel"""
        if note_id in self.note_manager.notes:
            note = self.note_manager.notes[note_id]
            
            # Navigate to note's page
            if note.page_number != self.pdf_handler.current_page + 1:
                self.go_to_page(note.page_number)
            
            # Highlight note's excerpt if available
            if note.excerpt:
                self.highlight_status_label.setText(f"📍 Note: {note.title}")
    
    def on_note_edit_requested(self, note_id: str):
        """Handle note edit request"""
        if note_id in self.note_manager.notes:
            note = self.note_manager.notes[note_id]
            
            dialog = HighlightDialog(note.excerpt, note.page_number, self)
            dialog.setWindowTitle(f"Edit Note: {note.title}")
            
            # Pre-fill dialog with existing data
            dialog.topic_combo.setCurrentText(
                self.note_manager.topics.get(note.topic_id, type('', (), {'name': 'General'})).name
            )
            dialog.title_input.setText(note.title)
            dialog.content_input.setPlainText(note.content)
            
            if dialog.exec() == dialog.DialogCode.Accepted:
                # Update note
                topic_name = dialog.topic_combo.currentText()
                topic_id = self.note_manager.get_or_create_topic(topic_name)
                
                # Update note data
                note.topic_id = topic_id
                note.title = dialog.title_input.text()
                note.content = dialog.content_input.toPlainText()
                
                # Save changes
                self.note_manager.update_note(note_id, note.content, note.title)
                self._load_document_notes()
                self._update_notes_stats()
    
    def on_note_created(self, note_id: str):
        """Handle note creation signal"""
        self._update_notes_stats()
    
    def on_note_updated(self, note_id: str):
        """Handle note update signal"""
        self._load_document_notes()
    
    def _render_current_page(self):
        """Render the current page with text data for highlighting"""
        if not self.pdf_handler.current_doc:
            return
        
        # Get page pixmap
        pixmap = self.pdf_handler.get_page_pixmap(
            self.pdf_handler.current_page,
            self.zoom_level
        )
        
        if pixmap:
            # Convert to QPixmap
            img_data = pixmap.tobytes("ppm")
            qpixmap = QPixmap()
            qpixmap.loadFromData(img_data)
            
            # Display in label
            self.pdf_label.setPixmap(qpixmap)
            self.pdf_label.resize(qpixmap.size())
            
            # Extract text data for highlighting
            self._extract_page_text_data()
            
            # Update page change signal
            self.page_changed.emit(self.pdf_handler.current_page + 1)
    
    def _extract_page_text_data(self):
        """Extract text blocks from current PDF page for selection"""
        if not self.pdf_handler.current_doc:
            return
        
        try:
            page = self.pdf_handler.current_doc[self.pdf_handler.current_page]
            text_dict = page.get_text("dict")
            
            # Set text data in highlightable label
            self.pdf_label.set_pdf_page_data(
                self.pdf_handler.current_page,
                text_dict.get("blocks", []),
                self.zoom_level
            )
        except Exception as e:
            print(f"Error extracting text data: {e}")
    
    def _load_document_notes(self):
        """Load notes for current document"""
        if not self.pdf_handler.document_id:
            return
        
        # Get notes for this document
        self.current_document_notes = self.note_manager.get_notes_by_document(
            self.pdf_handler.document_id
        )
        
        # Update notes panel
        self.notes_panel.update_notes_list(
            self.current_document_notes,
            self.note_manager.topics
        )
        
        # Update summary
        note_count = len(self.current_document_notes)
        self.notes_summary_label.setText(f"📝 {note_count} notes")
    
    def _load_page_highlights(self):
        """Load highlights for current page"""
        if not self.pdf_handler.document_id:
            return
        
        current_page = self.pdf_handler.current_page + 1
        page_notes = [
            note for note in self.current_document_notes 
            if note.page_number == current_page and note.excerpt
        ]
        
        # Clear existing highlights
        self.pdf_label.clear_highlights()
        
        # Add highlights for page notes
        for note in page_notes:
            if note.excerpt:
                # This is a simplified version - in practice, you'd need
                # to store and restore the exact highlight coordinates
                rect = self.pdf_label.rect()  # Placeholder rectangle
                self.pdf_label.add_highlight(note.excerpt, rect)
        
        self.clear_highlights_btn.setEnabled(len(page_notes) > 0)
    
    def _update_document_info(self):
        """Update document information display"""
        info = self.pdf_handler.get_document_info()
        
        if info:
            # Update title
            title = info.get('title', 'Unknown Document')
            if title == 'Unknown':
                title = os.path.basename(self.pdf_handler.current_doc.name)
            self.doc_title_label.setText(title)
            
            # Update details
            details = f"""
<b>Author:</b> {info.get('author', 'Unknown')}<br>
<b>Pages:</b> {info.get('total_pages', 0)}<br>
<b>Created:</b> {info.get('created', 'Unknown')[:10]}<br>
<b>Subject:</b> {info.get('subject', 'None')[:50]}
            """.strip()
            self.doc_details_text.setHtml(details)
            
            # Update progress
            progress = info.get('progress_percent', 0)
            self.progress_bar.setValue(int(progress))
            
            progress_text = f"""
Current Page: {info.get('current_page', 1)} / {info.get('total_pages', 0)}
Progress: {progress}%
            """.strip()
            self.progress_details.setText(progress_text)
    
    def _update_navigation_state(self):
        """Update navigation button states"""
        has_doc = self.pdf_handler.current_doc is not None
        
        # Enable/disable controls
        self.prev_btn.setEnabled(has_doc and self.pdf_handler.current_page > 0)
        self.next_btn.setEnabled(has_doc and self.pdf_handler.current_page < self.pdf_handler.total_pages - 1)
        self.page_spinbox.setEnabled(has_doc)
        self.zoom_in_btn.setEnabled(has_doc)
        self.zoom_out_btn.setEnabled(has_doc)
        
        # Note-taking controls
        self.highlight_mode_btn.setEnabled(has_doc)
        self.add_note_btn.setEnabled(has_doc)
        
        if has_doc:
            # Update page controls
            self.page_spinbox.setMaximum(self.pdf_handler.total_pages)
            self.page_spinbox.setValue(self.pdf_handler.current_page + 1)
            self.page_total_label.setText(f"/ {self.pdf_handler.total_pages}")
        else:
            self.page_spinbox.setMaximum(0)
            self.page_total_label.setText("/ 0")
    
    def _update_zoom_display(self):
        """Update zoom level display"""
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
    
    def _update_ui_state(self):
        """Update all UI state after page change"""
        self._update_navigation_state()
        self._update_document_info()
    
    def _update_stats_display(self):
        """Update reading statistics display - ENHANCED WITH ESTIMATION"""
        if not self.pdf_handler.current_doc:
            self.stats_display.setText("No active session")
            self.reading_time_label.setText("⏰ 0:00")
            return
        
        stats = self.pdf_handler.get_reading_stats()
        
        if stats:
            # Format session duration
            duration_min = stats.get('session_duration', 0)
            hours = int(duration_min // 60)
            minutes = int(duration_min % 60)
            time_str = f"{hours}:{minutes:02d}" if hours > 0 else f"{minutes}:00"
            
            # Build stats text
            stats_text = f"""
📊 Current Session:
Time: {time_str}
Pages Read: {stats.get('pages_read_this_session', 0)}
Reading Speed: {stats.get('reading_speed', 0):.1f} pages/min
Current Page Time: {stats.get('current_page_time', 0):.0f}s
            """.strip()
            
            # Add time estimation if available - ENHANCED
            if self.current_estimation:
                remaining_time = self.current_estimation.get("estimated_time_remaining_formatted", "Unknown")
                confidence = self.current_estimation.get("confidence_level", "Unknown")
                remaining_pages = self.current_estimation.get("remaining_pages", 0)
                
                estimation_text = f"""

🎯 Smart Estimates:
Remaining: {remaining_pages} pages
Time to finish: {remaining_time}
Confidence: {confidence}
Avg time/page: {self.current_estimation.get('avg_time_per_page_seconds', 0):.1f}s
                """.strip()
                
                stats_text += estimation_text
            else:
                stats_text += "\n\n⏱️ Building time estimates..."
            
            self.stats_display.setText(stats_text)
            self.reading_time_label.setText(f"⏰ {time_str}")
    
    def _update_notes_stats(self):
        """Update note-taking statistics"""
        if not self.current_document_notes:
            self.notes_stats_display.setText("No notes yet")
            return
        
        total_notes = len(self.current_document_notes)
        topics = set(note.topic_id for note in self.current_document_notes)
        pages_with_notes = set(note.page_number for note in self.current_document_notes)
        
        # Notes with excerpts (highlights)
        highlights = [note for note in self.current_document_notes if note.excerpt]
        
        stats_text = f"""
Total Notes: {total_notes}
Topics: {len(topics)}
Pages with Notes: {len(pages_with_notes)}
Highlights: {len(highlights)}
        """.strip()
        
        self.notes_stats_display.setText(stats_text)
    
    def _autosave_progress(self):
        """Auto-save reading progress"""
        if self.pdf_handler.current_doc:
            self.pdf_handler._save_progress()
            # Trigger estimation update after saving progress
            if self.time_estimator:
                QTimer.singleShot(500, self._update_time_estimation)
    
    def export_notes(self, export_path: str = None):
        """Export notes for current document"""
        if not self.current_document_notes:
            QMessageBox.information(self, "No Notes", "No notes to export for this document.")
            return
        
        if not export_path:
            export_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Notes",
                f"notes_{os.path.basename(self.pdf_handler.current_doc.name)}.md",
                "Markdown Files (*.md);;All Files (*)"
            )
        
        if export_path:
            try:
                # Export notes for current document
                exported_count = 0
                with open(export_path, 'w', encoding='utf-8') as f:
                    doc_info = self.pdf_handler.get_document_info()
                    f.write(f"# Notes for {doc_info.get('title', 'Document')}\n\n")
                    f.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
                    
                    # Add time estimation summary
                    if self.current_estimation:
                        f.write("## Reading Progress & Time Estimation\n\n")
                        f.write(f"- **Current Page**: {self.current_estimation.get('current_page', 0)} / {self.current_estimation.get('total_pages', 0)}\n")
                        f.write(f"- **Progress**: {self.current_estimation.get('progress_percent', 0):.1f}%\n")
                        f.write(f"- **Estimated time to finish**: {self.current_estimation.get('estimated_time_remaining_formatted', 'Unknown')}\n")
                        f.write(f"- **Reading speed**: {self.current_estimation.get('avg_time_per_page_seconds', 0):.1f} seconds per page\n\n")
                    
                    # Group notes by topic
                    from collections import defaultdict
                    notes_by_topic = defaultdict(list)
                    for note in self.current_document_notes:
                        topic_name = self.note_manager.topics.get(note.topic_id, type('', (), {'name': 'Unknown'})).name
                        notes_by_topic[topic_name].append(note)
                    
                    for topic_name, notes in notes_by_topic.items():
                        f.write(f"## {topic_name}\n\n")
                        for note in sorted(notes, key=lambda n: n.page_number):
                            f.write(f"### {note.title}\n\n")
                            if note.excerpt:
                                f.write(f"**Highlight:** _{note.excerpt}_\n\n")
                            if note.content:
                                f.write(f"{note.content}\n\n")
                            f.write(f"*Page {note.page_number}*\n\n---\n\n")
                            exported_count += 1
                
                QMessageBox.information(
                    self, 
                    "Export Complete", 
                    f"Successfully exported {exported_count} notes to {export_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export notes:\n{str(e)}")
    
    def get_time_estimation_summary(self) -> dict:
        """Get current time estimation summary for external use"""
        return self.current_estimation.copy() if self.current_estimation else {}
    
    def closeEvent(self, event):
        """Handle widget close event"""
        # Close time estimation resources
        if self.time_estimator:
            try:
                self.time_estimator.close()
            except:
                pass
        
        if self.reading_predictor:
            try:
                self.reading_predictor.close()
            except:
                pass
        
        if self.pdf_handler.current_doc:
            self.pdf_handler.close_pdf()
        
        super().closeEvent(event)