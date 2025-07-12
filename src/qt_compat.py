"""
Qt Compatibility Layer - PyQt6 Version
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

QT_LIB = "PyQt6"

# PyQt6 compatibility - map old constants to new enum structure
class QtCompat:
    # Alignment flags
    AlignCenter = Qt.AlignmentFlag.AlignCenter
    AlignLeft = Qt.AlignmentFlag.AlignLeft
    AlignRight = Qt.AlignmentFlag.AlignRight
    
    # Orientation
    Horizontal = Qt.Orientation.Horizontal
    Vertical = Qt.Orientation.Vertical
    
    # Key sequences
    StandardKey = QKeySequence.StandardKey

# Override Qt with compatibility layer
Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
Qt.AlignLeft = Qt.AlignmentFlag.AlignLeft  
Qt.AlignRight = Qt.AlignmentFlag.AlignRight
Qt.Horizontal = Qt.Orientation.Horizontal
Qt.Vertical = Qt.Orientation.Vertical

print("🎯 Using PyQt6 with compatibility layer")
