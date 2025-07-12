"""
SprintReader Notes Module
Obsidian-style note-taking with highlight-to-note functionality
"""

from .note_manager import NoteManager, Note, Topic
from .highlight_selector import HighlightableLabel, HighlightDialog, NotesPanel

__all__ = [
    'NoteManager', 
    'Note', 
    'Topic',
    'HighlightableLabel', 
    'HighlightDialog', 
    'NotesPanel'
]

__version__ = "4.0.0"
__description__ = "Local-first note-taking system with PDF highlighting integration"
