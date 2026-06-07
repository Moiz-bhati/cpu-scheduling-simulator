Merge branch 'tasks/hadi' into main

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
