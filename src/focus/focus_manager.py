"""
Focus Manager - Controls distraction-free reading mode
"""

from qt_compat import QObject, pyqtSignal, QSettings
from qt_compat import QWidget
from typing import Dict, List

class FocusManager(QObject):
    """Manages focus mode and distraction-free environment"""
    
    # Signals
    focus_mode_enabled = pyqtSignal()
    focus_mode_disabled = pyqtSignal()
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.is_focus_mode = False
        self.settings = QSettings('SprintReader', 'Focus')
        
        # Default focus settings
        self.focus_settings = {
            'hide_sidebar': True,
            'hide_toolbar': False,
            'hide_statusbar': True,
            'dim_background': True,
            'show_timer_overlay': True,
            'auto_hide_cursor': True,
            'minimal_notifications': True,
            'ambient_sounds': False
        }
        
        # Load saved settings
        self._load_settings()
        
        # Track hidden widgets for restoration
        self.hidden_widgets = []
        self.original_states = {}
    
    def enable_focus_mode(self, main_window):
        """Enable focus mode - hide distractions"""
        if self.is_focus_mode:
            return
        
        self.is_focus_mode = True
        self.hidden_widgets = []
        self.original_states = {}
        
        # Hide sidebar if setting enabled
        if self.focus_settings.get('hide_sidebar', True):
            sidebar = getattr(main_window, 'sidebar', None)
            if sidebar:
                self._hide_widget(sidebar)
        
        # Hide toolbar if setting enabled
        if self.focus_settings.get('hide_toolbar', False):
            toolbar = getattr(main_window, 'toolbar', None)
            if toolbar:
                self._hide_widget(toolbar)
        
        # Hide statusbar if setting enabled
        if self.focus_settings.get('hide_statusbar', True):
            statusbar = main_window.statusBar()
            if statusbar:
                self._hide_widget(statusbar)
        
        # Apply visual changes
        if self.focus_settings.get('dim_background', True):
            self._apply_focus_styling(main_window)
        
        self.focus_mode_enabled.emit()
    
    def disable_focus_mode(self, main_window):
        """Disable focus mode - restore hidden elements"""
        if not self.is_focus_mode:
            return
        
        self.is_focus_mode = False
        
        # Restore all hidden widgets
        for widget in self.hidden_widgets:
            widget.show()
        
        # Restore original states
        for widget, state in self.original_states.items():
            if hasattr(widget, 'setVisible'):
                widget.setVisible(state)
        
        # Remove focus styling
        self._remove_focus_styling(main_window)
        
        self.hidden_widgets = []
        self.original_states = {}
        self.focus_mode_disabled.emit()
    
    def toggle_focus_mode(self, main_window):
        """Toggle focus mode on/off"""
        if self.is_focus_mode:
            self.disable_focus_mode(main_window)
        else:
            self.enable_focus_mode(main_window)
    
    def update_setting(self, key: str, value):
        """Update a focus setting"""
        if key in self.focus_settings:
            self.focus_settings[key] = value
            self._save_settings()
            self.settings_changed.emit(self.focus_settings)
    
    def get_settings(self) -> Dict:
        """Get current focus settings"""
        return self.focus_settings.copy()
    
    def is_enabled(self) -> bool:
        """Check if focus mode is currently enabled"""
        return self.is_focus_mode
    
    def _hide_widget(self, widget: QWidget):
        """Hide widget and track for restoration"""
        if widget and widget.isVisible():
            self.original_states[widget] = widget.isVisible()
            self.hidden_widgets.append(widget)
            widget.hide()
    
    def _apply_focus_styling(self, main_window):
        """Apply focus mode visual styling"""
        # Dark, minimal styling for focus
        focus_style = """
        QMainWindow {
            background-color: #1e1e1e;
        }
        QScrollArea {
            background-color: #2d2d2d;
            border: none;
        }
        QLabel {
            background-color: #f8f8f8;
            border: 1px solid #333;
        }
        """
        main_window.setStyleSheet(focus_style)
    
    def _remove_focus_styling(self, main_window):
        """Remove focus mode styling"""
        main_window.setStyleSheet("")  # Reset to default
    
    def _load_settings(self):
        """Load focus settings from storage"""
        for key, default_value in self.focus_settings.items():
            value = self.settings.value(key, default_value, type=type(default_value))
            self.focus_settings[key] = value
    
    def _save_settings(self):
        """Save focus settings to storage"""
        for key, value in self.focus_settings.items():
            self.settings.setValue(key, value)
