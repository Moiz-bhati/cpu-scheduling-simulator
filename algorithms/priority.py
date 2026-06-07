"""
Priority Scheduling Algorithm (Non-preemptive)
Lower priority number = higher priority.
"""

import copy
from typing import List, Tuple
from models.process import Process, ProcessState


def priority_scheduling(processes: List[Process]) -> Tuple[List[dict], List[Process]]:
    procs = [copy.deepcopy(p) for p in processes]
    for p in procs:
        p.remaining_time = p.burst_time

    gantt = []
    current_time = 0
    completed = []
    remaining = list(procs)

    while remaining:
        available = [p for p in remaining if p.arrival_time <= current_time]
        if not available:
            current_time = min(p.arrival_time for p in remaining)
            available = [p for p in remaining if p.arrival_time <= current_time]

        # Lower priority number = higher priority
        selected = min(available, key=lambda p: (p.priority, p.arrival_time, p.pid))
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
