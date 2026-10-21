from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout


# Dark-only palette. Kept for compatibility with code that imports DARK.
DARK = {
    "background": "#171819",
    "surface": "#222426",
    "surface_alt": "#292B2E",
    "text": "#ECEDEB",
    "muted": "#A3A6A8",
    "border": "#3B3E41",
    "accent": "#A59BFF",
    "accent_soft": "#343047",
    "button": "#2B2D30",
    "button_hover": "#383B3E",
    "success": "#78D6A9",
    "warning": "#E8B66D",
    "danger": "#FF9292",
}


def set_dark_mode(widget):
    """Apply the application's permanent dark theme."""
    widget.setStyleSheet("""
        QWidget {
            background-color: #171819;
            color: #ECEDEB;
            font-family: "Segoe UI", Arial;
            font-size: 13px;
        }

        QLabel {
            background: transparent;
            color: #ECEDEB;
        }

        QPushButton {
            background-color: #2B2D30;
            color: #ECEDEB;
            border: 1px solid #3B3E41;
            border-radius: 7px;
            padding: 8px 12px;
        }

        QPushButton:hover {
            background-color: #383B3E;
        }

        QTableWidget, QTextEdit, QPlainTextEdit, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QListWidget,
        QTreeWidget, QTableView {
            background-color: #222426;
            color: #ECEDEB;
            border: 1px solid #3B3E41;
            border-radius: 8px;
            selection-background-color: #343047;
            selection-color: #FFFFFF;
        }

        QTableWidget {
            alternate-background-color: #292B2E;
            gridline-color: #3B3E41;
        }

        QHeaderView::section {
            background-color: #2B2D30;
            color: #ECEDEB;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #3B3E41;
        }

        QTabWidget::pane {
            border: 1px solid #3B3E41;
            background-color: #171819;
        }

        QTabBar::tab {
            background-color: #222426;
            color: #A3A6A8;
            padding: 9px 16px;
            margin-right: 3px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }

        QTabBar::tab:selected {
            background-color: #343047;
            color: #ECEDEB;
            border-bottom: 2px solid #A59BFF;
        }

        QGroupBox {
            border: 1px solid #3B3E41;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            color: #A59BFF;
        }

        QScrollBar:vertical {
            background: #222426;
            width: 11px;
            margin: 2px;
        }

        QScrollBar::handle:vertical {
            background: #55595D;
            border-radius: 5px;
            min-height: 25px;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }

        QScrollBar:horizontal {
            background: #222426;
            height: 11px;
            margin: 2px;
        }

        QScrollBar::handle:horizontal {
            background: #55595D;
            border-radius: 5px;
            min-width: 25px;
        }

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0;
        }
    """)


class ThemeSwitch(QPushButton):
    """Legacy compatibility class; the app now uses dark mode only."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(False)
        self.setFixedSize(54, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setText("D")
        self.setToolTip("Dark mode is always enabled")
        self.setStyleSheet("""
            QPushButton {
                background-color: #343047;
                color: #ECEDEB;
                border: 1px solid #5A547A;
                border-radius: 14px;
                padding: 0px;
                font-weight: bold;
            }
        """)


def create_theme_switch(central_widget, on_theme_changed=None):
    """
    Compatibility wrapper for existing app.py.
    It applies dark mode permanently and returns a small DARK label layout.
    The callback is invoked once with True so chart widgets can sync to dark mode.
    """
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.setAlignment(
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    )

    label = QLabel("DARK")
    label.setStyleSheet("color: #A3A6A8; font-weight: 600;")
    layout.addWidget(label)

    set_dark_mode(central_widget)

    if on_theme_changed:
        on_theme_changed(True)

    return layout
