"""
Simulation Panel - Center panel with Gantt chart, CPU status, ready queue,
process state diagram, and playback controls.
"""

import os
import tempfile
from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QSpinBox, QGroupBox, QScrollArea,
    QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QPainterPath,
    QLinearGradient, QFontMetrics
)

from models.process import ProcessState, STATE_COLORS, PROCESS_COLORS


# ---------------------------------------------------------------------------
# Gantt Chart Widget
# ---------------------------------------------------------------------------

class GanttWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gantt: List[dict] = []
        self.color_map: dict = {}
        self.current_step: int = -1
        self.setMinimumHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, gantt, color_map, current_step=-1):
        self.gantt = gantt
        self.color_map = color_map
        self.current_step = current_step
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_h = 44
        bar_y = 24

        painter.fillRect(0, 0, w, h, QColor("#0F1923"))

        if not self.gantt:
            painter.setPen(QColor("#7F8C8D"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Run simulation to see Gantt chart")
            return

        total_time = self.gantt[-1]["end"]
        start_time = self.gantt[0]["start"]
        span = total_time - start_time
        if span == 0:
            return

        margin_l, margin_r = 10, 10
        usable_w = w - margin_l - margin_r

        def time_to_x(t):
            return margin_l + (t - start_time) / span * usable_w

        # Draw idle gaps
        for i, block in enumerate(self.gantt):
            if i > 0:
                prev_end = self.gantt[i - 1]["end"]
                if block["start"] > prev_end:
                    x1 = time_to_x(prev_end)
                    x2 = time_to_x(block["start"])
                    painter.fillRect(int(x1), bar_y, max(1, int(x2 - x1)), bar_h,
                                     QColor("#1A2332"))
                    painter.setPen(QColor("#7F8C8D"))
                    painter.setFont(QFont("Segoe UI", 7))
                    painter.drawText(int((x1+x2)//2 - 10), bar_y + bar_h // 2 + 4, "idle")

        # Draw blocks
        for i, block in enumerate(self.gantt):
            x1 = time_to_x(block["start"])
            x2 = time_to_x(block["end"])
            bw = max(2, x2 - x1)
            color = QColor(self.color_map.get(block["pid"], "#3498DB"))

            is_current = (i == self.current_step)
            alpha = 255 if is_current or self.current_step == -1 else 160

            # Gradient fill
            grad = QLinearGradient(x1, bar_y, x1, bar_y + bar_h)
            c_light = QColor(color)
            c_light.setAlpha(alpha)
            c_dark = QColor(color.darker(160))
            c_dark.setAlpha(alpha)
            grad.setColorAt(0, c_light)
            grad.setColorAt(1, c_dark)

            path = QPainterPath()
            path.addRoundedRect(QRectF(x1 + 1, bar_y, bw - 2, bar_h), 4, 4)
            painter.fillPath(path, grad)

            if is_current:
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                painter.drawPath(path)
            else:
                painter.setPen(QPen(QColor("#0F1923"), 1))
                painter.drawPath(path)

            # Label
            if bw > 18:
                painter.setPen(QColor("#FFFFFF" if is_current else "#ECF0F1"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                label_rect = QRectF(x1 + 1, bar_y, bw - 2, bar_h)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, block["pid"])

        # Time labels
        painter.setPen(QColor("#7F8C8D"))
        painter.setFont(QFont("Segoe UI", 7))
        tick_times = set()
        for block in self.gantt:
            tick_times.add(block["start"])
            tick_times.add(block["end"])

        last_x = -999
        for t in sorted(tick_times):
            x = time_to_x(t)
            if x - last_x > 18:
                painter.drawLine(int(x), bar_y + bar_h, int(x), bar_y + bar_h + 4)
                painter.drawText(int(x) - 6, bar_y + bar_h + 14, str(t))
                last_x = x


# ---------------------------------------------------------------------------
# Process State Diagram
# ---------------------------------------------------------------------------

class ProcessStateDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc_states: dict = {}
        self.color_map: dict = {}
        self.setMinimumHeight(70)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_states(self, proc_states, color_map):
        self.proc_states = proc_states
        self.color_map = color_map
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#0F1923"))

        if not self.proc_states:
            painter.setPen(QColor("#7F8C8D"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Process states will appear here")
            return

        states_order = [ProcessState.NEW, ProcessState.READY, ProcessState.RUNNING,
                        ProcessState.WAITING, ProcessState.TERMINATED]
        state_labels = {
            ProcessState.NEW: "NEW",
            ProcessState.READY: "READY",
            ProcessState.RUNNING: "RUNNING",
            ProcessState.WAITING: "WAITING",
            ProcessState.TERMINATED: "DONE",
        }

        # Group processes by state
        groups = {s: [] for s in states_order}
        for pid, state in self.proc_states.items():
            groups[state].append(pid)

        n_states = len(states_order)
        cell_w = self.width() // n_states
        box_h = 40
        y = (self.height() - box_h) // 2

        for i, state in enumerate(states_order):
            x = i * cell_w
            color = QColor(STATE_COLORS[state])

            # State box
            bg = QColor(color)
            bg.setAlpha(40)
            painter.fillRect(x + 4, y, cell_w - 8, box_h, bg)
            painter.setPen(QPen(color, 1))
            painter.drawRect(x + 4, y, cell_w - 8, box_h)

            # State name
            painter.setPen(color)
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.drawText(x + 4, y, cell_w - 8, 14, Qt.AlignmentFlag.AlignCenter, state_labels[state])

            # Process PIDs in this state
            pids_text = ", ".join(groups[state]) if groups[state] else "—"
            painter.setPen(QColor("#ECF0F1"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(x + 4, y + 14, cell_w - 8, box_h - 14, Qt.AlignmentFlag.AlignCenter, pids_text)

            # Arrow between states (except last)
            if i < n_states - 1:
                ax = x + cell_w - 4
                ay = y + box_h // 2
                painter.setPen(QPen(QColor("#3D4C5E"), 1))
                painter.drawLine(ax, ay, ax + 8, ay)
                # Arrowhead
                painter.setBrush(QBrush(QColor("#3D4C5E")))
                pts_x = [ax + 8, ax + 4, ax + 4]
                pts_y = [ay, ay - 4, ay + 4]
                from PyQt6.QtCore import QPoint
                from PyQt6.QtGui import QPolygon
                poly = QPolygon([QPoint(pts_x[k], pts_y[k]) for k in range(3)])
                painter.drawPolygon(poly)


# ---------------------------------------------------------------------------
# Ready Queue Widget
# ---------------------------------------------------------------------------

class ReadyQueueWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue: List[str] = []
        self.color_map: dict = {}
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_queue(self, queue, color_map):
        self.queue = queue
        self.color_map = color_map
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#0F1923"))

        painter.setPen(QColor("#F39C12"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(8, 0, 100, 20, Qt.AlignmentFlag.AlignVCenter, "Ready Queue:")

        if not self.queue:
            painter.setPen(QColor("#7F8C8D"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(120, 0, self.width() - 120, 48, Qt.AlignmentFlag.AlignVCenter, "[ empty ]")
            return

        x = 120
        for pid in self.queue:
            color = QColor(self.color_map.get(pid, "#F39C12"))
            # Box
            bw = 42
            painter.fillRect(x, 8, bw, 32, QColor(color.red(), color.green(), color.blue(), 60))
            painter.setPen(QPen(color, 1.5))
            painter.drawRect(x, 8, bw, 32)
            # Label
            painter.setPen(QColor("#ECF0F1"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(x, 8, bw, 32, Qt.AlignmentFlag.AlignCenter, pid)
            x += bw + 6


# ---------------------------------------------------------------------------
# Main Simulation Panel
# ---------------------------------------------------------------------------

class SimulationPanel(QWidget):
    algorithm_changed = pyqtSignal(str, int)   # algo name, quantum
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    step_forward = pyqtSignal()
    step_backward = pyqtSignal()
    speed_changed = pyqtSignal(int)
    compare_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Algorithm selector row
        algo_group = QGroupBox("Algorithm Configuration")
        algo_group.setStyleSheet(self._group_style())
        algo_row = QHBoxLayout(algo_group)
        algo_row.setSpacing(10)

        algo_lbl = QLabel("Algorithm:")
        algo_lbl.setStyleSheet("color: #BDC3C7; font-size: 11px;")
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            "FCFS", "SJF", "SRTF", "Priority",
            "Preemptive Priority", "Round Robin", "Multilevel Queue"
        ])
        self.algo_combo.setStyleSheet(self._combo_style())
        self.algo_combo.currentTextChanged.connect(self._on_algo_changed)

        self.quantum_lbl = QLabel("Quantum:")
        self.quantum_lbl.setStyleSheet("color: #BDC3C7; font-size: 11px;")
        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 100)
        self.quantum_spin.setValue(2)
        self.quantum_spin.setStyleSheet(self._spin_style())
        self.quantum_spin.setFixedWidth(60)

        self.compare_btn = QPushButton("⚖ Compare All")
        self.compare_btn.setStyleSheet(self._btn_style("#8E44AD", "#9B59B6"))
        self.compare_btn.clicked.connect(self.compare_requested)

        algo_row.addWidget(algo_lbl)
        algo_row.addWidget(self.algo_combo)
        algo_row.addWidget(self.quantum_lbl)
        algo_row.addWidget(self.quantum_spin)
        algo_row.addStretch()
        algo_row.addWidget(self.compare_btn)
        layout.addWidget(algo_group)

        # Hide quantum initially
        self.quantum_lbl.setVisible(False)
        self.quantum_spin.setVisible(False)

        # CPU Status indicator
        cpu_row = QHBoxLayout()
        self.cpu_status = QFrame()
        self.cpu_status.setStyleSheet("""
            background: #1A2332; border: 1px solid #3D4C5E;
            border-radius: 6px; padding: 4px;
        """)
        cpu_layout = QHBoxLayout(self.cpu_status)
        cpu_layout.setContentsMargins(12, 6, 12, 6)

        self.cpu_label = QLabel("CPU Status")
        self.cpu_label.setStyleSheet("color: #7F8C8D; font-size: 10px; font-weight: bold;")

        self.cpu_running = QLabel("Idle")
        self.cpu_running.setStyleSheet("color: #27AE60; font-size: 16px; font-weight: bold;")
        self.cpu_running.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cpu_time = QLabel("Time: 0")
        self.cpu_time.setStyleSheet("color: #BDC3C7; font-size: 11px;")

        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addStretch()
        cpu_layout.addWidget(self.cpu_running)
        cpu_layout.addStretch()
        cpu_layout.addWidget(self.cpu_time)
        cpu_row.addWidget(self.cpu_status, stretch=1)

        # Time progress bar
        self.time_bar = QProgressBar()
        self.time_bar.setRange(0, 100)
        self.time_bar.setValue(0)
        self.time_bar.setFixedWidth(140)
        self.time_bar.setFixedHeight(36)
        self.time_bar.setStyleSheet("""
            QProgressBar {
                background: #1A2332; border: 1px solid #3D4C5E; border-radius: 4px;
                color: #ECF0F1; font-weight: bold; font-size: 10px; text-align: center;
            }
            QProgressBar::chunk { background: #2980B9; border-radius: 3px; }
        """)
        cpu_row.addWidget(self.time_bar)
        layout.addLayout(cpu_row)

        # Gantt chart
        gantt_group = QGroupBox("Gantt Chart")
        gantt_group.setStyleSheet(self._group_style())
        gantt_layout = QVBoxLayout(gantt_group)
        gantt_layout.setContentsMargins(6, 6, 6, 6)
        self.gantt_widget = GanttWidget()
        gantt_layout.addWidget(self.gantt_widget)
        layout.addWidget(gantt_group)

        # Ready queue
        rq_group = QGroupBox("Ready Queue")
        rq_group.setStyleSheet(self._group_style())
        rq_layout = QVBoxLayout(rq_group)
        rq_layout.setContentsMargins(6, 6, 6, 6)
        self.ready_queue_widget = ReadyQueueWidget()
        rq_layout.addWidget(self.ready_queue_widget)
        layout.addWidget(rq_group)

        # Process state diagram
        state_group = QGroupBox("Process State Transitions")
        state_group.setStyleSheet(self._group_style())
        state_layout = QVBoxLayout(state_group)
        state_layout.setContentsMargins(6, 6, 6, 6)
        self.state_diagram = ProcessStateDiagram()
        state_layout.addWidget(self.state_diagram)
        layout.addWidget(state_group)

        # Simulation controls
        ctrl_group = QGroupBox("Simulation Controls")
        ctrl_group.setStyleSheet(self._group_style())
        ctrl_layout = QVBoxLayout(ctrl_group)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.start_btn = QPushButton("▶ Start")
        self.pause_btn = QPushButton("⏸ Pause")
        self.resume_btn = QPushButton("▶ Resume")
        self.reset_btn = QPushButton("⟳ Reset")
        self.prev_btn = QPushButton("◀ Prev")
        self.next_btn = QPushButton("▶ Next")

        self.start_btn.setStyleSheet(self._btn_style("#27AE60", "#2ECC71"))
        self.pause_btn.setStyleSheet(self._btn_style("#E67E22", "#F39C12"))
        self.resume_btn.setStyleSheet(self._btn_style("#2980B9", "#3498DB"))
        self.reset_btn.setStyleSheet(self._btn_style("#C0392B", "#E74C3C"))
        self.prev_btn.setStyleSheet(self._btn_style("#7F8C8D", "#95A5A6"))
        self.next_btn.setStyleSheet(self._btn_style("#7F8C8D", "#95A5A6"))

        self.start_btn.clicked.connect(self.start_requested)
        self.pause_btn.clicked.connect(self.pause_requested)
        self.resume_btn.clicked.connect(self.resume_requested)
        self.reset_btn.clicked.connect(self.reset_requested)
        self.prev_btn.clicked.connect(self.step_backward)
        self.next_btn.clicked.connect(self.step_forward)

        for btn in [self.start_btn, self.prev_btn, self.next_btn,
                    self.pause_btn, self.resume_btn, self.reset_btn]:
            btn_row.addWidget(btn)
        ctrl_layout.addLayout(btn_row)

        # Speed slider
        speed_row = QHBoxLayout()
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: #BDC3C7; font-size: 10px;")
        speed_row.addWidget(speed_label)

        slow_lbl = QLabel("Slow")
        slow_lbl.setStyleSheet("color: #7F8C8D; font-size: 9px;")
        fast_lbl = QLabel("Fast")
        fast_lbl.setStyleSheet("color: #7F8C8D; font-size: 9px;")

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2C3E50; height: 4px; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #3498DB; width: 14px; height: 14px;
                margin: -5px 0; border-radius: 7px;
            }
            QSlider::sub-page:horizontal { background: #3498DB; border-radius: 2px; }
        """)
        self.speed_slider.valueChanged.connect(self.speed_changed)

        speed_row.addWidget(slow_lbl)
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(fast_lbl)
        ctrl_layout.addLayout(speed_row)
        layout.addWidget(ctrl_group)

        self._update_btn_states(running=False, paused=False)

    def _on_algo_changed(self, algo):
        needs_quantum = algo in ("Round Robin", "Multilevel Queue")
        self.quantum_lbl.setVisible(needs_quantum)
        self.quantum_spin.setVisible(needs_quantum)
        self.algorithm_changed.emit(algo, self.quantum_spin.value())

    def get_algorithm(self):
        return self.algo_combo.currentText()

    def get_quantum(self):
        return self.quantum_spin.value()

    def update_step(self, state: dict, color_map: dict, total_steps: int):
        if not state:
            return

        running_pid = state.get("running_pid", "Idle")
        current_time = state.get("current_time", 0)
        ready_queue = state.get("ready_queue", [])
        proc_states = state.get("proc_states", {})
        gantt_so_far = state.get("gantt_so_far", [])
        step = state.get("step", 0)

        self.cpu_running.setText(f"Running: {running_pid}")
        self.cpu_time.setText(f"Time: {current_time}")

        if total_steps > 0:
            self.time_bar.setValue(int((step + 1) / total_steps * 100))
            self.time_bar.setFormat(f"Step {step + 1}/{total_steps}")

        self.gantt_widget.set_data(gantt_so_far, color_map, step)
        self.ready_queue_widget.set_queue(ready_queue, color_map)
        self.state_diagram.set_states(proc_states, color_map)

    def set_full_gantt(self, gantt, color_map):
        """Show complete Gantt (after simulation finishes)."""
        self.gantt_widget.set_data(gantt, color_map, -1)

    def reset_display(self):
        self.gantt_widget.set_data([], {}, -1)
        self.ready_queue_widget.set_queue([], {})
        self.state_diagram.set_states({}, {})
        self.cpu_running.setText("Idle")
        self.cpu_time.setText("Time: 0")
        self.time_bar.setValue(0)
        self.time_bar.setFormat("")

    def _update_btn_states(self, running, paused):
        self.start_btn.setEnabled(not running)
        self.pause_btn.setEnabled(running and not paused)
        self.resume_btn.setEnabled(running and paused)
        self.reset_btn.setEnabled(True)

    def _group_style(self):
        return """
            QGroupBox {
                color: #ECF0F1; font-weight: bold; font-size: 11px;
                border: 1px solid #3D4C5E; border-radius: 6px;
                margin-top: 8px; padding-top: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; }
        """

    def _combo_style(self):
        return """
            QComboBox {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; border-radius: 4px;
                padding: 5px 10px; font-size: 11px; min-width: 160px;
            }
            QComboBox:focus { border: 1px solid #3498DB; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3498DB; selection-background-color: #2980B9;
            }
        """

    def _spin_style(self):
        return """
            QSpinBox {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; border-radius: 4px;
                padding: 4px 6px; font-size: 11px;
            }
            QSpinBox:focus { border: 1px solid #3498DB; }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #2C3E50; border: none; width: 14px;
            }
        """

    def _btn_style(self, base, hover):
        return f"""
            QPushButton {{
                background: {base}; color: white; border: none;
                border-radius: 5px; padding: 6px 10px;
                font-weight: bold; font-size: 10px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:disabled {{ background: #2C3E50; color: #7F8C8D; }}
        """
