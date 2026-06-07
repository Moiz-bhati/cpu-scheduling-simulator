"""
Statistics Panel - Right panel showing per-process and aggregate metrics.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from models.process import Process, PROCESS_COLORS


class StatsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("📊 Statistics")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #3498DB; padding: 4px 0;")
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(10)

        # Process metrics table
        proc_group = QGroupBox("Per Process Metrics")
        proc_group.setStyleSheet(self._group_style())
        proc_layout = QVBoxLayout(proc_group)

        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "CT", "WT", "TAT", "RT"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.proc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.proc_table.setStyleSheet(self._table_style())
        self.proc_table.setMinimumHeight(150)
        proc_layout.addWidget(self.proc_table)
        self.content_layout.addWidget(proc_group)

        # Overall metrics
        overall_group = QGroupBox("Overall Metrics")
        overall_group.setStyleSheet(self._group_style())
        overall_layout = QVBoxLayout(overall_group)

        self.metrics_widgets = {}
        metric_defs = [
            ("avg_waiting_time", "Avg Waiting Time", "#E74C3C"),
            ("avg_turnaround_time", "Avg Turnaround", "#F39C12"),
            ("avg_response_time", "Avg Response Time", "#9B59B6"),
            ("cpu_utilization", "CPU Utilization %", "#27AE60"),
            ("throughput", "Throughput", "#3498DB"),
        ]
        for key, label, color in metric_defs:
            row = QFrame()
            row.setStyleSheet(f"background: #1A2332; border-radius: 4px; border-left: 3px solid {color};")
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(10, 6, 10, 6)
            row_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; background: transparent; border: none;")

            val = QLabel("—")
            val.setStyleSheet("color: #ECF0F1; font-size: 16px; font-weight: bold; background: transparent; border: none;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)

            row_layout.addWidget(lbl)
            row_layout.addWidget(val)
            overall_layout.addWidget(row)
            self.metrics_widgets[key] = val

        self.content_layout.addWidget(overall_group)

        # Process state legend
        state_group = QGroupBox("Process State Legend")
        state_group.setStyleSheet(self._group_style())
        state_layout = QVBoxLayout(state_group)

        states = [
            ("NEW", "#9B59B6"),
            ("READY", "#F39C12"),
            ("RUNNING", "#27AE60"),
            ("WAITING", "#E67E22"),
            ("TERMINATED", "#3498DB"),
        ]
        for state_name, color in states:
            row = QFrame()
            row.setStyleSheet("background: transparent; border: none;")
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            indicator = QFrame()
            indicator.setFixedHeight(26)
            indicator.setStyleSheet(f"""
                background: {color}22;
                border: 1px solid {color};
                border-radius: 4px;
            """)
            ind_layout = QVBoxLayout(indicator)
            ind_layout.setContentsMargins(8, 0, 0, 0)
            lbl = QLabel(f"● {state_name}")
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; background: transparent; border: none;")
            ind_layout.addWidget(lbl)
            state_layout.addWidget(indicator)

        self.content_layout.addWidget(state_group)
        self.content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _group_style(self):
        return """
            QGroupBox {
                color: #ECF0F1; font-weight: bold; font-size: 11px;
                border: 1px solid #3D4C5E; border-radius: 6px;
                margin-top: 8px; padding-top: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; }
        """

    def _table_style(self):
        return """
            QTableWidget {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; border-radius: 4px;
                gridline-color: #2C3E50; font-size: 10px;
            }
            QTableWidget::item:selected { background: #2980B9; }
            QHeaderView::section {
                background: #2C3E50; color: #3498DB;
                font-weight: bold; padding: 4px;
                border: none; border-bottom: 1px solid #3D4C5E;
                font-size: 10px;
            }
            QScrollBar:vertical { background: #1A2332; width: 6px; }
            QScrollBar::handle:vertical { background: #3D4C5E; border-radius: 3px; }
        """

    def update_results(self, processes, metrics):
        # Per-process table
        self.proc_table.setRowCount(len(processes))
        for i, p in enumerate(processes):
            color = QColor(PROCESS_COLORS[i % len(PROCESS_COLORS)])
            vals = [
                p.pid,
                str(p.completion_time or "—"),
                str(p.waiting_time or "0"),
                str(p.turnaround_time or "—"),
                str(p.response_time or "0"),
            ]
            for j, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 0:
                    item.setForeground(color)
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.proc_table.setItem(i, j, item)

        # Overall metrics
        if metrics:
            self.metrics_widgets["avg_waiting_time"].setText(f"{metrics.get('avg_waiting_time', 0):.2f}")
            self.metrics_widgets["avg_turnaround_time"].setText(f"{metrics.get('avg_turnaround_time', 0):.2f}")
            self.metrics_widgets["avg_response_time"].setText(f"{metrics.get('avg_response_time', 0):.2f}")
            self.metrics_widgets["cpu_utilization"].setText(f"{metrics.get('cpu_utilization', 0):.1f}%")
            self.metrics_widgets["throughput"].setText(f"{metrics.get('throughput', 0):.4f}")

    def clear_results(self):
        self.proc_table.setRowCount(0)
        for w in self.metrics_widgets.values():
            w.setText("—")
