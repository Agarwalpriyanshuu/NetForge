"""
NetForge's application-wide visual theme.

Applies a dark base palette (via ``pyqtdarktheme``, already listed as
a project dependency but never previously wired up) and layers
NetForge-specific design tokens on top of it -- accent color,
navigation rail, cards, tab bars, tables, status bar.

Every selector here is scoped to a Qt object name or dynamic
``class`` property set explicitly by the widgets that want it, so
this stylesheet never reaches into the SSH terminal viewport: that
widget paints its own colors directly from
:mod:`netforge.core.terminal.colors` and must stay independent of the
app chrome's theme.
"""

from __future__ import annotations

import qdarktheme
from PySide6.QtWidgets import QApplication

ACCENT = "#3b8eea"
ACCENT_HOVER = "#2f78d1"
ACCENT_PRESSED = "#255f9e"

SURFACE = "#1e1e1e"
SURFACE_RAISED = "#252526"
BORDER = "#3c3c3c"

TEXT_MUTED = "#9d9d9d"
SUCCESS = "#23d18b"
DANGER = "#f14c4c"
WARNING = "#e5c07b"

_NETFORGE_QSS = f"""
QWidget#navigationRail {{
    background-color: {SURFACE};
    border: none;
    border-right: 1px solid {BORDER};
    outline: 0;
    padding-top: 8px;
}}

QListWidget#navigationRail::item {{
    border-radius: 8px;
    margin: 4px 10px;
    padding: 10px 0px;
    color: {TEXT_MUTED};
    font-size: 18px;
}}

QListWidget#navigationRail::item:selected {{
    background-color: {ACCENT};
    color: white;
}}

QListWidget#navigationRail::item:hover:!selected {{
    background-color: {SURFACE_RAISED};
    color: white;
}}

QWidget#sidebar {{
    background-color: {SURFACE_RAISED};
    border: none;
    border-right: 1px solid {BORDER};
    padding-top: 8px;
}}

QLabel#pageTitle {{
    font-size: 22px;
    font-weight: 600;
    padding: 4px 0px 8px 0px;
}}

QFrame[class="card"] {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QFrame[class="card"]:hover {{
    border: 1px solid {ACCENT};
}}

QFrame[class="section"] {{
    background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px;
}}

QPushButton[class="primary"] {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 600;
}}

QPushButton[class="primary"]:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton[class="primary"]:pressed {{
    background-color: {ACCENT_PRESSED};
}}

QPushButton[class="primary"]:disabled {{
    background-color: {BORDER};
    color: {TEXT_MUTED};
}}

QTabWidget#workspaceTabs::pane {{
    border: none;
    border-top: 1px solid {BORDER};
}}

QTabWidget#sshSessionTabs::pane {{
    border: none;
    border-top: 1px solid {BORDER};
}}

QTabBar::tab {{
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background-color: {SURFACE_RAISED};
    border-bottom: 2px solid {ACCENT};
}}

QTableView {{
    gridline-color: {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    alternate-background-color: {SURFACE_RAISED};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

QHeaderView::section {{
    background-color: {SURFACE_RAISED};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}

QStatusBar#netforgeStatusBar {{
    border-top: 1px solid {BORDER};
}}

QLabel[class="emptyState"] {{
    color: {TEXT_MUTED};
    font-size: 14px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply NetForge's dark theme to the whole application."""
    base_stylesheet = qdarktheme.load_stylesheet(theme="dark")
    app.setStyleSheet(base_stylesheet + "\n" + _NETFORGE_QSS)
