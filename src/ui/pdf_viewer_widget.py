"""
SprintReader PDF Viewer Widget
PyQt6 widget for displaying PDF content with time estimation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QSpinBox, QFileDialog, QSplitter, QTextEdit, 
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import fitz  # PyMuPDF
import os
from typing import Optional
from pdf_handler.pdf_handler import PDFHandler

class PDFViewerWidget(QWidget):
    """Main PDF viewer widget with navigation and controls"""
    
    # Signals
    page_changed = pyqtSignal(int)  # Emitted when page changes
    document_opened = pyqtSignal(str)  # Emitted when document opens
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_handler = PDFHandler()
        self.zoom_level = 1.0
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self.current_zoom_index = 2  # Start at 1.0x
        
        # Timer for auto-save
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._autosave_progress)
        self.autosave_timer.start(30000)  # Auto-save every 30 seconds
        
        # Timer for updating reading stats
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats_display)
        self.stats_timer.start(1000)  # Update every second
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create toolbar
        self.create_toolbar(main_layout)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar for document info and controls
        self.create_sidebar(splitter)
        
        # Right side for PDF display
        self.create_pdf_display(splitter)
        
        # Set splitter proportions (sidebar: 25%, PDF: 75%)
        splitter.setSizes([300, 900])
        
        # Status bar
        self.create_status_bar(main_layout)
        
        # Initially disable navigation controls
        self._update_navigation_state()
    
    def create_toolbar(self, parent_layout):
        """Create the main toolbar"""
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
        
        # Stretch to push remaining items to the right
        toolbar_layout.addStretch()
        
        # Session controls
        self.session_label = QLabel("📚 No Document")
        toolbar_layout.addWidget(self.session_label)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_sidebar(self, splitter):
        """Create the left sidebar with document info and stats"""
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Document Information
        doc_info_group = QGroupBox("📄 Document Info")
        doc_info_layout = QVBoxLayout(doc_info_group)
        
        self.doc_title_label = QLabel("No document loaded")
        self.doc_title_label.setWordWrap(True)
        font = QFont()
        font.setBold(True)
        self.doc_title_label.setFont(font)
        doc_info_layout.addWidget(self.doc_title_label)
        
        self.doc_details_text = QTextEdit()
        self.doc_details_text.setMaximumHeight(120)
        self.doc_details_text.setReadOnly(True)
        doc_info_layout.addWidget(self.doc_details_text)
        
        sidebar_layout.addWidget(doc_info_group)
        
        # Reading Progress
        progress_group = QGroupBox("📊 Reading Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_details = QTextEdit()
        self.progress_details.setMaximumHeight(100)
        self.progress_details.setReadOnly(True)
        progress_layout.addWidget(self.progress_details)
        
        sidebar_layout.addWidget(progress_group)
        
        # Reading Statistics
        stats_group = QGroupBox("⏱️ Session Stats")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_display = QTextEdit()
        self.stats_display.setMaximumHeight(150)
        self.stats_display.setReadOnly(True)
        stats_layout.addWidget(self.stats_display)
        
        sidebar_layout.addWidget(stats_group)
        
        # Add stretch to push everything to top
        sidebar_layout.addStretch()
        
        splitter.addWidget(sidebar)
    
    def create_pdf_display(self, splitter):
        """Create the main PDF display area"""
        # Create scroll area for PDF
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # PDF display label
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                margin: 10px;
            }
        """)
        self.pdf_label.setText("📖 Open a PDF file to start reading")
        self.pdf_label.setMinimumSize(400, 600)
        
        self.scroll_area.setWidget(self.pdf_label)
        splitter.addWidget(self.scroll_area)
    
    def create_status_bar(self, parent_layout):
        """Create the status bar"""
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready to load PDF")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.reading_time_label = QLabel("⏰ 0:00")
        status_layout.addWidget(self.reading_time_label)
        
        parent_layout.addLayout(status_layout)
    
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
        """Load a PDF file"""
        if self.pdf_handler.open_pdf(file_path):
            # Update UI
            self._update_document_info()
            self._update_navigation_state()
            self._render_current_page()
            
            # Emit signal
            self.document_opened.emit(file_path)
            
            # Update status
            filename = os.path.basename(file_path)
            self.status_label.setText(f"Loaded: {filename}")
            self.session_label.setText(f"📚 {filename}")
        else:
            self.status_label.setText("❌ Failed to load PDF")
    
    def previous_page(self):
        """Go to previous page"""
        if self.pdf_handler.previous_page():
            self._render_current_page()
            self._update_ui_state()
    
    def next_page(self):
        """Go to next page"""
        if self.pdf_handler.next_page():
            self._render_current_page()
            self._update_ui_state()
    
    def go_to_page(self, page_num: int):
        """Go to specific page (1-based)"""
        if self.pdf_handler.go_to_page(page_num - 1):  # Convert to 0-based
            self._render_current_page()
            self._update_ui_state()
    
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
    
    def _render_current_page(self):
        """Render the current page"""
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
            
            # Update page change signal
            self.page_changed.emit(self.pdf_handler.current_page + 1)
    
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
        """Update reading statistics display with time estimation"""
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
Session Time: {time_str}
Pages Read: {stats.get('pages_read_this_session', 0)}
Reading Speed: {stats.get('reading_speed', 0):.1f} pages/min
Current Page Time: {stats.get('current_page_time', 0):.0f}s
            """.strip()
            
            # Add time estimation if document is loaded
            if self.pdf_handler.document_id:
                try:
                    from estimation.time_estimator import TimeEstimator
                    estimator = TimeEstimator()
                    estimate = estimator.estimate_document_completion(self.pdf_handler.document_id)
                    
                    if estimate:
                        remaining_time = estimate.get("estimated_time_remaining_formatted", "Unknown")
                        confidence = estimate.get("confidence_level", "Unknown")
                        
                        estimation_text = f"""

🎯 Smart Estimates:
Time to finish: {remaining_time}
Confidence: {confidence}
                        """.strip()
                        
                        stats_text += estimation_text
                    
                    estimator.close()
                except Exception as e:
                    pass  # Estimation failed, continue without it
            
            self.stats_display.setText(stats_text)
            self.reading_time_label.setText(f"⏰ {time_str}")
    
    def _autosave_progress(self):
        """Auto-save reading progress"""
        if self.pdf_handler.current_doc:
            self.pdf_handler._save_progress()
    
    def closeEvent(self, event):
        """Handle widget close event"""
        if self.pdf_handler.current_doc:
            self.pdf_handler.close_pdf()
        super().closeEvent(event)
