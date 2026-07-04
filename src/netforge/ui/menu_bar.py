from PySide6.QtGui import QAction


def create_menu(window):

    menu = window.menuBar()

    file_menu = menu.addMenu("&File")
    edit_menu = menu.addMenu("&Edit")
    view_menu = menu.addMenu("&View")
    tools_menu = menu.addMenu("&Tools")
    window_menu = menu.addMenu("&Window")
    help_menu = menu.addMenu("&Help")

    exit_action = QAction("Exit", window)
    exit_action.triggered.connect(window.close)

    file_menu.addSeparator()
    file_menu.addAction(exit_action)