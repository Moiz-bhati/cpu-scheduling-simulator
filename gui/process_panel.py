"""
Process Panel - Left panel for adding/managing processes.
"""

import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QGroupBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from models.process import Process, PROCESS_COLORS


class ProcessPanel(QWidget):
    processes_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.processes = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        title = QLabel("⚙ Process Manager")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #3498DB; padding: 4px 0;")
        layout.addWidget(title)

        # Input form
        form_group = QGroupBox("Add Process")
        form_group.setStyleSheet("""
            QGroupBox {
                color: #ECF0F1; font-weight: bold; font-size: 11px;
                border: 1px solid #3D4C5E; border-radius: 6px;
                margin-top: 8px; padding-top: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; }
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(6)

        # PID row
        pid_row = QHBoxLayout()
        pid_label = QLabel("PID:")
        pid_label.setFixedWidth(70)
        pid_label.setStyleSheet("color: #BDC3C7;")
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("e.g. P1")
        self.pid_input.setMaxLength(6)
        self._style_input(self.pid_input)
        pid_row.addWidget(pid_label)
        pid_row.addWidget(self.pid_input)
        form_layout.addLayout(pid_row)

        # Arrival time row
        arr_row = QHBoxLayout()
        arr_label = QLabel("Arrival:")
        arr_label.setFixedWidth(70)
        arr_label.setStyleSheet("color: #BDC3C7;")
        self.arrival_spin = QSpinBox()
        self.arrival_spin.setRange(0, 9999)
        self._style_spin(self.arrival_spin)
        arr_row.addWidget(arr_label)
        arr_row.addWidget(self.arrival_spin)
        form_layout.addLayout(arr_row)

        # Burst time row
        burst_row = QHBoxLayout()
        burst_label = QLabel("Burst:")
        burst_label.setFixedWidth(70)
        burst_label.setStyleSheet("color: #BDC3C7;")
        self.burst_spin = QSpinBox()
        self.burst_spin.setRange(1, 9999)
        self.burst_spin.setValue(4)
        self._style_spin(self.burst_spin)
        burst_row.addWidget(burst_label)
        burst_row.addWidget(self.burst_spin)
        form_layout.addLayout(burst_row)

        # Priority row
        pri_row = QHBoxLayout()
        pri_label = QLabel("Priority:")
        pri_label.setFixedWidth(70)
        pri_label.setStyleSheet("color: #BDC3C7;")
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 99)
        self.priority_spin.setToolTip("Lower number = higher priority")
        self._style_spin(self.priority_spin)
        pri_row.addWidget(pri_label)
        pri_row.addWidget(self.priority_spin)
        form_layout.addLayout(pri_row)

        # Queue level row
        ql_row = QHBoxLayout()
        ql_label = QLabel("Queue Lvl:")
        ql_label.setFixedWidth(70)
        ql_label.setStyleSheet("color: #BDC3C7;")
        self.queue_spin = QSpinBox()
        self.queue_spin.setRange(0, 9)
        self.queue_spin.setToolTip("Queue level for Multilevel Queue (0 = highest)")
        self._style_spin(self.queue_spin)
        ql_row.addWidget(ql_label)
        ql_row.addWidget(self.queue_spin)
        form_layout.addLayout(ql_row)

        layout.addWidget(form_group)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)

        self.add_btn = QPushButton("➕  Add Process")
        self.add_btn.clicked.connect(self._add_process)
        self.add_btn.setStyleSheet(self._btn_style("#27AE60", "#2ECC71"))

        self.delete_btn = QPushButton("🗑  Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        self.delete_btn.setStyleSheet(self._btn_style("#C0392B", "#E74C3C"))

        self.clear_btn = QPushButton("✖  Clear All")
        self.clear_btn.clicked.connect(self._clear_all)
        self.clear_btn.setStyleSheet(self._btn_style("#7F8C8D", "#95A5A6"))

        self.sample_btn = QPushButton("📂  Load Sample Data")
        self.sample_btn.clicked.connect(self._load_sample)
        self.sample_btn.setStyleSheet(self._btn_style("#2980B9", "#3498DB"))

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.sample_btn)
        layout.addLayout(btn_layout)

        # Process table
        table_label = QLabel("Process List")
        table_label.setStyleSheet("color: #BDC3C7; font-weight: bold; margin-top: 4px;")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["PID", "Arrival", "Burst", "Priority", "Q.Lvl"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; border-radius: 4px;
                gridline-color: #2C3E50;
            }
            QTableWidget::item:selected { background: #2980B9; }
            QHeaderView::section {
                background: #2C3E50; color: #3498DB;
                font-weight: bold; padding: 5px;
                border: none; border-bottom: 1px solid #3D4C5E;
            }
            QScrollBar:vertical { background: #1A2332; width: 8px; }
            QScrollBar::handle:vertical { background: #3D4C5E; border-radius: 4px; }
        """)
        layout.addWidget(self.table)

        # Count label
        self.count_label = QLabel("0 processes")
        self.count_label.setStyleSheet("color: #7F8C8D; font-size: 10px;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        # Enter key shortcut
        self.pid_input.returnPressed.connect(self._add_process)

        # Auto-increment PID
        self._auto_pid = 1

    def _style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; border-radius: 4px;
                padding: 5px 8px; font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid #3498DB; }
        """)

    def _style_spin(self, widget):
        widget.setStyleSheet("""
            QSpinBox {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; border-radius: 4px;
                padding: 4px 6px; font-size: 11px;
            }
            QSpinBox:focus { border: 1px solid #3498DB; }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #2C3E50; border: none; width: 16px;
            }
            QSpinBox::up-arrow { image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent; border-bottom: 5px solid #3498DB; }
            QSpinBox::down-arrow { image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent; border-top: 5px solid #3498DB; }
        """)

    def _btn_style(self, base, hover):
        return f"""
            QPushButton {{
                background: {base}; color: white;
                border: none; border-radius: 5px;
                padding: 7px 10px; font-weight: bold; font-size: 11px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:pressed {{ background: {base}; }}
        """

    def _add_process(self):
        pid = self.pid_input.text().strip()
        if not pid:
            pid = f"P{self._auto_pid}"

        # Check duplicate PID
        if any(p.pid == pid for p in self.processes):
            QMessageBox.warning(self, "Duplicate PID", f"Process '{pid}' already exists.")
            return

        proc = Process(
            pid=pid,
            arrival_time=self.arrival_spin.value(),
            burst_time=self.burst_spin.value(),
            priority=self.priority_spin.value(),
            queue_level=self.queue_spin.value(),
        )
        self.processes.append(proc)
        self._auto_pid += 1
        self.pid_input.setText(f"P{self._auto_pid}")
        self.arrival_spin.setValue(0)
        self.burst_spin.setValue(4)
        self.priority_spin.setValue(0)
        self.queue_spin.setValue(0)
        self._refresh_table()
        self.processes_changed.emit(self.processes)

    def _delete_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = self.table.currentRow()
        if 0 <= row < len(self.processes):
            self.processes.pop(row)
            self._refresh_table()
            self.processes_changed.emit(self.processes)

    def _clear_all(self):
        self.processes.clear()
        self._auto_pid = 1
        self._refresh_table()
        self.processes_changed.emit(self.processes)

    def _load_sample(self):
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "sample_processes.json"
        )
        try:
            with open(sample_path) as f:
                data = json.load(f)
            self.processes = [Process.from_dict(d) for d in data["processes"]]
            self._auto_pid = len(self.processes) + 1
            self._refresh_table()
            self.processes_changed.emit(self.processes)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load sample data:\n{e}")

    def _refresh_table(self):
        self.table.setRowCount(len(self.processes))
        for i, p in enumerate(self.processes):
            color = QColor(PROCESS_COLORS[i % len(PROCESS_COLORS)])
            items = [p.pid, str(p.arrival_time), str(p.burst_time), str(p.priority), str(p.queue_level)]
            for j, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 0:
                    item.setForeground(color)
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(i, j, item)
        self.count_label.setText(f"{len(self.processes)} process{'es' if len(self.processes) != 1 else ''}")

    def set_processes(self, processes):
        self.processes = processes
        self._refresh_table()

    def get_processes(self):
        return self.processes
