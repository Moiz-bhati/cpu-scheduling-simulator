"""
SJF - Shortest Job First Scheduling Algorithm (Non-preemptive)
Among available processes, the one with shortest burst time executes first.
"""

import copy
from typing import List, Tuple
from models.process import Process, ProcessState


def sjf(processes: List[Process]) -> Tuple[List[dict], List[Process]]:
    procs = [copy.deepcopy(p) for p in processes]
    for p in procs:
        p.remaining_time = p.burst_time

    gantt = []
    current_time = 0
    completed = []
    remaining = list(procs)

    while remaining:
        # Find available processes
        available = [p for p in remaining if p.arrival_time <= current_time]
        if not available:
            current_time = min(p.arrival_time for p in remaining)
            available = [p for p in remaining if p.arrival_time <= current_time]

        # Pick shortest burst time (ties broken by arrival, then PID)
        selected = min(available, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        remaining.remove(selected)

        selected.start_time = current_time
        selected.response_time = current_time - selected.arrival_time
        gantt.append({"pid": selected.pid, "start": current_time, "end": current_time + selected.burst_time})
        current_time += selected.burst_time
        selected.completion_time = current_time
        selected.turnaround_time = selected.completion_time - selected.arrival_time
        selected.waiting_time = selected.turnaround_time - selected.burst_time
        selected.state = ProcessState.TERMINATED
        completed.append(selected)

    return gantt, completed
