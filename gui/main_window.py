"""
Main Window - Top-level application window that orchestrates all panels.
"""

import json
import os
import tempfile

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QMenuBar, QFileDialog,
    QMessageBox, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QFont, QColor

from models.process import Process, PROCESS_COLORS
from simulation.scheduler_engine import SchedulerEngine
from gui.process_panel import ProcessPanel
from gui.simulation_panel import SimulationPanel
from gui.stats_panel import StatsPanel
from gui.comparison_window import ComparisonWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = SchedulerEngine()
        self._is_running = False
        self._is_paused = False
        self._current_step = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._auto_step)
        self._speed = 5

        self.setWindowTitle("CPU Scheduling Visualizer Pro  |  Operating Systems Simulator")
        self.setMinimumSize(1280, 760)
        self.resize(1440, 860)
        self._apply_theme()
        self._setup_menu()
        self._setup_ui()
        self._setup_status_bar()

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: #0F1923; }
            QSplitter::handle { background: #2C3E50; }
            QMenuBar {
                background: #0A1520; color: #ECF0F1;
                font-size: 11px; border-bottom: 1px solid #2C3E50;
            }
            QMenuBar::item:selected { background: #2C3E50; }
            QMenu {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #2C3E50;
            }
            QMenu::item:selected { background: #2980B9; }
            QStatusBar { background: #0A1520; color: #7F8C8D; font-size: 10px; }
            QScrollBar:vertical { background: #1A2332; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #3D4C5E; border-radius: 4px; }
        """)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")
        save_action = QAction("💾  Save Simulation", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_simulation)
        file_menu.addAction(save_action)

        load_action = QAction("📂  Load Simulation", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_simulation)
        file_menu.addAction(load_action)

        file_menu.addSeparator()
        export_action = QAction("📄  Export PDF Report", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_pdf)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        quit_action = QAction("✖  Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Simulation
        sim_menu = menubar.addMenu("Simulation")
        start_action = QAction("▶  Start", self)
        start_action.setShortcut("Space")
        start_action.triggered.connect(self._on_start)
        sim_menu.addAction(start_action)

        reset_action = QAction("⟳  Reset", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._on_reset)
        sim_menu.addAction(reset_action)

        sim_menu.addSeparator()
        compare_action = QAction("⚖  Compare All Algorithms", self)
        compare_action.triggered.connect(self._on_compare)
        sim_menu.addAction(compare_action)

        # Help
        help_menu = menubar.addMenu("Help")
        about_action = QAction("ℹ  About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet("background: #0A1520; border-bottom: 1px solid #2C3E50;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("⚡  CPU Scheduling Visualizer Pro")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #3498DB;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        subtitle = QLabel("Operating Systems Semester Project  |  All 7 Algorithms")
        subtitle.setStyleSheet("color: #7F8C8D; font-size: 10px;")
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header)

        # Splitter with three panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        self.process_panel = ProcessPanel()
        self.process_panel.setMinimumWidth(220)
        self.process_panel.setMaximumWidth(320)
        self.process_panel.processes_changed.connect(self._on_processes_changed)

        self.sim_panel = SimulationPanel()
        self.sim_panel.algorithm_changed.connect(self._on_algo_changed)
        self.sim_panel.start_requested.connect(self._on_start)
        self.sim_panel.pause_requested.connect(self._on_pause)
        self.sim_panel.resume_requested.connect(self._on_resume)
        self.sim_panel.reset_requested.connect(self._on_reset)
        self.sim_panel.step_forward.connect(self._on_step_forward)
        self.sim_panel.step_backward.connect(self._on_step_backward)
        self.sim_panel.speed_changed.connect(self._on_speed_changed)
        self.sim_panel.compare_requested.connect(self._on_compare)

        self.stats_panel = StatsPanel()
        self.stats_panel.setMinimumWidth(200)
        self.stats_panel.setMaximumWidth(300)

        splitter.addWidget(self.process_panel)
        splitter.addWidget(self.sim_panel)
        splitter.addWidget(self.stats_panel)
        splitter.setSizes([260, 880, 260])
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready  |  Add processes and click Start to simulate")
        self.status_bar.addWidget(self.status_label)

        self.algo_status = QLabel("")
        self.algo_status.setStyleSheet("color: #3498DB; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.algo_status)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot(list)
    def _on_processes_changed(self, processes):
        self.engine.set_processes(processes)
        self._on_reset()
        self.status_label.setText(f"{len(processes)} process(es) loaded")

    @pyqtSlot(str, int)
    def _on_algo_changed(self, algo, quantum):
        self.engine.algorithm = algo
        self.engine.quantum = quantum
        self.algo_status.setText(f"Algorithm: {algo}  |  Quantum: {quantum}")

    def _on_start(self):
        processes = self.process_panel.get_processes()
        if not processes:
            QMessageBox.warning(self, "No Processes", "Please add at least one process before starting the simulation.")
            return

        self.engine.set_processes(processes)
        self.engine.algorithm = self.sim_panel.get_algorithm()
        self.engine.quantum = self.sim_panel.get_quantum()
        self.engine.run()

        if not self.engine.gantt:
            QMessageBox.information(self, "Empty Result", "Simulation produced no output.")
            return

        self._current_step = 0
        self._is_running = True
        self._is_paused = False
        self._start_timer()
        self.status_label.setText(f"▶ Running {self.engine.algorithm}...")
        self.algo_status.setText(f"Algorithm: {self.engine.algorithm}")

    def _on_pause(self):
        self._is_paused = True
        self._timer.stop()
        self.status_label.setText("⏸ Paused")

    def _on_resume(self):
        if self._is_running and self._is_paused:
            self._is_paused = False
            self._start_timer()
            self.status_label.setText(f"▶ Resumed {self.engine.algorithm}...")

    def _on_reset(self):
        self._timer.stop()
        self._is_running = False
        self._is_paused = False
        self._current_step = 0
        self.sim_panel.reset_display()
        self.stats_panel.clear_results()
        self.status_label.setText("Ready  |  Add processes and click Start to simulate")

    def _on_step_forward(self):
        if not self.engine.gantt:
            self._on_start()
            return
        if self._current_step < self.engine.total_steps - 1:
            self._current_step += 1
            self._render_step(self._current_step)

    def _on_step_backward(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._render_step(self._current_step)

    def _on_speed_changed(self, val):
        self._speed = val
        if self._is_running and not self._is_paused:
            self._timer.stop()
            self._start_timer()

    def _on_compare(self):
        processes = self.process_panel.get_processes()
        if not processes:
            QMessageBox.warning(self, "No Processes", "Please add at least one process.")
            return
        self.engine.set_processes(processes)
        self.engine.quantum = self.sim_panel.get_quantum()
        results = self.engine.run_all_algorithms()
        if not results:
            QMessageBox.information(self, "Error", "Could not compute comparison.")
            return
        dlg = ComparisonWindow(results, self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_timer(self):
        interval = max(100, 1100 - self._speed * 100)
        self._timer.start(interval)

    def _auto_step(self):
        if self._current_step >= self.engine.total_steps:
            self._timer.stop()
            self._is_running = False
            self._finish_simulation()
            return

        self._render_step(self._current_step)
        self._current_step += 1

    def _render_step(self, step):
        state = self.engine.get_step_state(step)
        self.sim_panel.update_step(state, self.engine._color_map, self.engine.total_steps)

    def _finish_simulation(self):
        self.sim_panel.set_full_gantt(self.engine.gantt, self.engine._color_map)
        metrics = self.engine.compute_metrics()
        self.stats_panel.update_results(self.engine.result_procs, metrics)
        self.status_label.setText(f"✔ {self.engine.algorithm} simulation complete  |  {len(self.engine.result_procs)} processes")

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _save_simulation(self):
        processes = self.process_panel.get_processes()
        if not processes:
            QMessageBox.warning(self, "Nothing to Save", "No processes to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Simulation", "simulation.json", "JSON Files (*.json)")
        if not path:
            return
        data = {
            "algorithm": self.sim_panel.get_algorithm(),
            "quantum": self.sim_panel.get_quantum(),
            "processes": [p.to_dict() for p in processes],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self.status_label.setText(f"✔ Saved to {os.path.basename(path)}")

    def _load_simulation(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Simulation", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            processes = [Process.from_dict(d) for d in data.get("processes", [])]
            self.process_panel.set_processes(processes)
            self.engine.set_processes(processes)
            self.status_label.setText(f"✔ Loaded {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load file:\n{e}")

    def _export_pdf(self):
        try:
            from reports.pdf_generator import generate_pdf_report, REPORTLAB_AVAILABLE
        except ImportError:
            REPORTLAB_AVAILABLE = False

        if not self.engine.result_procs:
            QMessageBox.warning(self, "Nothing to Export", "Run a simulation first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", "report.json", "PDF Files (*.pdf)")
        if not path:
            return

        # Save Gantt chart as temp image if matplotlib is available
        gantt_img = None
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches

            fig, ax = plt.subplots(figsize=(10, 2))
            fig.patch.set_facecolor("#0F1923")
            ax.set_facecolor("#1A2332")

            gantt = self.engine.gantt
            if gantt:
                span = gantt[-1]["end"] - gantt[0]["start"]
                for block in gantt:
                    color = self.engine._color_map.get(block["pid"], "#3498DB")
                    ax.barh(0, block["end"] - block["start"], left=block["start"],
                            color=color, edgecolor="#0F1923", height=0.6)
                    ax.text((block["start"] + block["end"]) / 2, 0, block["pid"],
                            ha="center", va="center", color="white", fontsize=8, fontweight="bold")

            ax.set_yticks([])
            ax.tick_params(axis='x', colors='#ECF0F1')
            ax.spines[:].set_color('#3D4C5E')
            gantt_img = tempfile.mktemp(suffix=".png")
            plt.savefig(gantt_img, bbox_inches="tight", facecolor="#0F1923")
            plt.close()
        except Exception:
            pass

        metrics = self.engine.compute_metrics()
        try:
            comparison = self.engine.run_all_algorithms()
        except Exception:
            comparison = None

        from reports.pdf_generator import generate_pdf_report
        ok = generate_pdf_report(
            self.engine.result_procs,
            self.engine.algorithm,
            self.engine.gantt,
            metrics,
            comparison,
            path,
            gantt_img,
        )

        if ok:
            self.status_label.setText(f"✔ PDF exported to {os.path.basename(path)}")
            QMessageBox.information(self, "PDF Exported", f"Report saved to:\n{path}")
        else:
            QMessageBox.warning(self, "Export Failed",
                                "PDF export failed.\nInstall reportlab: pip install reportlab")

    def _show_about(self):
        QMessageBox.about(self, "About",
            "<h3>CPU Scheduling Visualizer Pro</h3>"
            "<p>An educational desktop application for simulating and visualizing "
            "CPU scheduling algorithms.</p>"
            "<p><b>Algorithms:</b> FCFS, SJF, SRTF, Priority, Preemptive Priority, "
            "Round Robin, Multilevel Queue</p>"
            "<p><b>Technologies:</b> Python 3, PyQt6, Matplotlib, ReportLab</p>"
            "<p>Operating Systems Semester Project</p>"
        )
