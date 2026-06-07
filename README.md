# CPU Scheduling Visualizer Pro

A professional desktop application for simulating and visualizing CPU scheduling algorithms.  
**Operating Systems Semester Project** | Python 3 + PyQt6

---

## Features

- **7 Scheduling Algorithms**: FCFS, SJF, SRTF, Priority, Preemptive Priority, Round Robin, Multilevel Queue
- **Real-time Gantt Chart** with color-coded process blocks
- **Step-by-step simulation** with forward/backward navigation
- **Process State Transitions**: NEW → READY → RUNNING → WAITING → TERMINATED
- **Ready Queue Visualization** updated live during simulation
- **Performance Metrics**: Waiting Time, Turnaround Time, Response Time, CPU Utilization, Throughput
- **Algorithm Comparison Mode**: Compare all algorithms with bar charts and rankings
- **PDF Report Generation** with process tables, Gantt chart, and metrics
- **Save/Load** simulations as JSON
- **Dark Professional UI** with blue accents

---

## Installation

```bash
pip install PyQt6 matplotlib pandas reportlab
```

---

## Running the Application

```bash
cd cpu_scheduler_visualizer
python main.py
```

---

## Project Structure

```
cpu_scheduler_visualizer/
├── main.py                         # Application entry point
├── README.md
├── gui/
│   ├── main_window.py              # Main application window
│   ├── process_panel.py            # Left panel: process management
│   ├── simulation_panel.py         # Center panel: Gantt, controls, state
│   ├── stats_panel.py              # Right panel: metrics & statistics
│   └── comparison_window.py        # Algorithm comparison dialog
├── algorithms/
│   ├── fcfs.py                     # First Come First Serve
│   ├── sjf.py                      # Shortest Job First
│   ├── srtf.py                     # Shortest Remaining Time First
│   ├── round_robin.py              # Round Robin
│   ├── priority.py                 # Priority Scheduling
│   ├── preemptive_priority.py      # Preemptive Priority
│   └── multilevel_queue.py         # Multilevel Queue
├── models/
│   └── process.py                  # Process data model & states
├── simulation/
│   └── scheduler_engine.py         # Core simulation engine
├── reports/
│   └── pdf_generator.py            # PDF report generation
├── data/
│   └── sample_processes.json       # Sample process set
└── assets/
    └── icons/
```

---

## Usage Guide

1. **Add Processes** in the left panel (PID, Arrival, Burst, Priority)
2. **Select Algorithm** from the dropdown in the center panel
3. Click **Start** to begin the animated simulation
4. Use **Pause / Resume / Next / Prev** for step-by-step control
5. Adjust **Speed** with the slider
6. Click **Compare All** to see all algorithm results side-by-side
7. Use **File → Export PDF Report** to generate a report

---

## Algorithms

| Algorithm | Type | Key Property |
|-----------|------|-------------|
| FCFS | Non-preemptive | Arrival order |
| SJF | Non-preemptive | Shortest burst first |
| SRTF | Preemptive | Shortest remaining time |
| Priority | Non-preemptive | Lower number = higher priority |
| Preemptive Priority | Preemptive | Higher priority interrupts |
| Round Robin | Preemptive | Fixed time quantum |
| Multilevel Queue | Preemptive | Queue levels + Round Robin |

---

## Metrics

- **CT** – Completion Time
- **WT** – Waiting Time = TAT − Burst Time
- **TAT** – Turnaround Time = CT − Arrival Time
- **RT** – Response Time = First CPU time − Arrival Time
- **CPU Utilization** – % of time CPU was busy
- **Throughput** – Processes completed per time unit
