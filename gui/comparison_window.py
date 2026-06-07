"""
Comparison Window - Shows bar charts and rankings comparing all algorithms.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB = True
except ImportError:
    MATPLOTLIB = False


ALGO_COLORS = {
    "FCFS": "#3498DB",
    "SJF": "#27AE60",
    "SRTF": "#2ECC71",
    "Priority": "#E74C3C",
    "Preemptive Priority": "#E67E22",
    "Round Robin": "#9B59B6",
    "Multilevel Queue": "#1ABC9C",
}


class ComparisonWindow(QDialog):
    def __init__(self, comparison_data: dict, parent=None):
        super().__init__(parent)
        self.data = comparison_data
        self.setWindowTitle("Algorithm Comparison — CPU Scheduling Visualizer Pro")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("background: #0F1923; color: #ECF0F1;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("⚖  Algorithm Comparison Dashboard")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #3498DB; padding-bottom: 8px;")
        layout.addWidget(title)

        # Best algorithm badge
        best_algo = min(self.data.items(), key=lambda x: x[1].get("avg_waiting_time", 9999))[0]
        badge = QLabel(f"🏆  Best Algorithm (Lowest Avg Waiting Time): {best_algo}")
        badge.setStyleSheet("""
            background: #27AE6033; color: #2ECC71;
            border: 1px solid #27AE60; border-radius: 6px;
            padding: 8px 14px; font-weight: bold; font-size: 12px;
        """)
        layout.addWidget(badge)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3D4C5E; border-radius: 4px; }
            QTabBar::tab {
                background: #1A2332; color: #BDC3C7;
                padding: 8px 18px; border: 1px solid #3D4C5E;
                border-bottom: none; border-radius: 4px 4px 0 0; font-size: 11px;
            }
            QTabBar::tab:selected { background: #2C3E50; color: #3498DB; font-weight: bold; }
        """)

        # Tab 1: Table
        table_tab = QWidget()
        table_tab.setStyleSheet("background: #0F1923;")
        table_layout = QVBoxLayout(table_tab)
        table = self._build_table()
        table_layout.addWidget(table)
        tabs.addTab(table_tab, "📋 Table")

        # Tab 2: Bar Charts
        if MATPLOTLIB:
            chart_tab = QWidget()
            chart_tab.setStyleSheet("background: #0F1923;")
            chart_layout = QVBoxLayout(chart_tab)
            canvas = self._build_charts()
            chart_layout.addWidget(canvas)
            tabs.addTab(chart_tab, "📊 Bar Charts")
        else:
            no_chart = QWidget()
            lbl = QLabel("Install matplotlib for charts: pip install matplotlib")
            lbl.setStyleSheet("color: #E74C3C; padding: 20px;")
            QVBoxLayout(no_chart).addWidget(lbl)
            tabs.addTab(no_chart, "📊 Bar Charts")

        # Tab 3: Ranking
        rank_tab = QWidget()
        rank_tab.setStyleSheet("background: #0F1923;")
        rank_layout = QVBoxLayout(rank_tab)
        rank_layout.addWidget(self._build_ranking())
        tabs.addTab(rank_tab, "🏆 Rankings")

        layout.addWidget(tabs)

    def _build_table(self):
        algos = list(self.data.keys())
        table = QTableWidget(len(algos), 5)
        table.setHorizontalHeaderLabels(["Algorithm", "Avg WT", "Avg TAT", "Avg RT", "CPU Util %"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget {
                background: #1A2332; color: #ECF0F1;
                border: 1px solid #3D4C5E; gridline-color: #2C3E50;
            }
            QTableWidget::item:selected { background: #2980B9; }
            QHeaderView::section {
                background: #2C3E50; color: #3498DB; font-weight: bold;
                padding: 6px; border: none; border-bottom: 1px solid #3D4C5E;
            }
        """)

        best_wt = min(self.data.values(), key=lambda x: x.get("avg_waiting_time", 9999))["avg_waiting_time"]

        for i, (algo, metrics) in enumerate(self.data.items()):
            vals = [
                algo,
                f"{metrics.get('avg_waiting_time', 0):.2f}",
                f"{metrics.get('avg_turnaround_time', 0):.2f}",
                f"{metrics.get('avg_response_time', 0):.2f}",
                f"{metrics.get('cpu_utilization', 0):.1f}%",
            ]
            color = QColor(ALGO_COLORS.get(algo, "#3498DB"))
            for j, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 0:
                    item.setForeground(color)
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if j == 1 and abs(metrics.get("avg_waiting_time", 0) - best_wt) < 0.001:
                    item.setBackground(QColor("#27AE6044"))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                table.setItem(i, j, item)

        return table

    def _build_charts(self):
        algos = list(self.data.keys())
        metrics_keys = ["avg_waiting_time", "avg_turnaround_time", "avg_response_time", "cpu_utilization"]
        metric_labels = ["Avg Waiting Time", "Avg Turnaround", "Avg Response Time", "CPU Utilization %"]

        fig = Figure(figsize=(10, 7), facecolor="#0F1923")
        axes = fig.subplots(2, 2)
        fig.subplots_adjust(hspace=0.5, wspace=0.35)

        bar_colors = [ALGO_COLORS.get(a, "#3498DB") for a in algos]

        for idx, (key, label) in enumerate(zip(metrics_keys, metric_labels)):
            ax = axes[idx // 2][idx % 2]
            ax.set_facecolor("#1A2332")
            vals = [self.data[a].get(key, 0) for a in algos]
            bars = ax.bar(range(len(algos)), vals, color=bar_colors, edgecolor="#0F1923", linewidth=0.5)

            # Highlight best
            best_val = min(vals) if key != "cpu_utilization" else max(vals)
            for bar, val in zip(bars, vals):
                if abs(val - best_val) < 0.001:
                    bar.set_edgecolor("#FFFFFF")
                    bar.set_linewidth(2)

            ax.set_xticks(range(len(algos)))
            short_labels = [a.replace("Preemptive Priority", "Pre.Pri").replace("Multilevel Queue", "MLQ") for a in algos]
            ax.set_xticklabels(short_labels, rotation=25, ha="right", fontsize=7, color="#BDC3C7")
            ax.set_title(label, color="#3498DB", fontsize=9, fontweight="bold", pad=6)
            ax.tick_params(axis='y', colors='#BDC3C7', labelsize=7)
            ax.spines['bottom'].set_color('#3D4C5E')
            ax.spines['left'].set_color('#3D4C5E')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.yaxis.grid(True, color='#2C3E50', linewidth=0.5)
            ax.set_axisbelow(True)

            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.02,
                        f'{val:.1f}', ha='center', va='bottom', fontsize=7, color='#ECF0F1')

        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background: #0F1923;")
        return canvas

    def _build_ranking(self):
        container = QWidget()
        container.setStyleSheet("background: #0F1923;")
        layout = QVBoxLayout(container)

        metrics = [
            ("avg_waiting_time", "Avg Waiting Time", False),
            ("avg_turnaround_time", "Avg Turnaround", False),
            ("avg_response_time", "Avg Response Time", False),
            ("cpu_utilization", "CPU Utilization", True),
        ]

        for key, label, higher_better in metrics:
            lbl = QLabel(f"🔢 Ranking by {label}:")
            lbl.setStyleSheet("color: #3498DB; font-weight: bold; font-size: 11px; margin-top: 8px;")
            layout.addWidget(lbl)

            sorted_algos = sorted(self.data.items(),
                                  key=lambda x: x[1].get(key, 9999),
                                  reverse=higher_better)

            medals = ["🥇", "🥈", "🥉"]
            for rank, (algo, m) in enumerate(sorted_algos):
                medal = medals[rank] if rank < 3 else f"  {rank+1}."
                row = QFrame()
                row.setStyleSheet(f"""
                    background: {ALGO_COLORS.get(algo, '#3498DB')}22;
                    border: 1px solid {ALGO_COLORS.get(algo, '#3498DB')}66;
                    border-radius: 4px; margin: 1px 0;
                """)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(10, 4, 10, 4)
                lbl2 = QLabel(f"{medal}  {algo}")
                lbl2.setStyleSheet(f"color: {ALGO_COLORS.get(algo, '#3498DB')}; font-weight: bold; background: transparent; border: none;")
                val_lbl = QLabel(f"{m.get(key, 0):.2f}")
                val_lbl.setStyleSheet("color: #ECF0F1; background: transparent; border: none;")
                row_layout.addWidget(lbl2)
                row_layout.addStretch()
                row_layout.addWidget(val_lbl)
                layout.addWidget(row)

        layout.addStretch()
        return container
