"""
CPU Scheduling Visualizer Pro
Entry point for the application.

Run: python main.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CPU Scheduling Visualizer Pro")
    app.setApplicationVersion("1.0.0")

    # High DPI
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Apply app-wide dark palette
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
