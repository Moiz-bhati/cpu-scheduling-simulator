"""
FCFS - First Come First Serve Scheduling Algorithm (Non-preemptive)
Processes execute in order of arrival time.
"""

import copy
from typing import List, Tuple
from models.process import Process, ProcessState


def fcfs(processes: List[Process]) -> Tuple[List[dict], List[Process]]:
    """
    Execute FCFS scheduling.
    Returns:
        gantt: List of {pid, start, end} dicts
        result: List of completed Process objects with metrics
    """
    procs = [copy.deepcopy(p) for p in processes]
    for p in procs:
        p.remaining_time = p.burst_time

    # Sort by arrival time (ties broken by PID)
    procs.sort(key=lambda p: (p.arrival_time, p.pid))

    gantt = []
    current_time = 0

    for p in procs:
        if current_time < p.arrival_time:
            current_time = p.arrival_time
        p.start_time = current_time
        p.response_time = current_time - p.arrival_time
        gantt.append({"pid": p.pid, "start": current_time, "end": current_time + p.burst_time})
        current_time += p.burst_time
        p.completion_time = current_time
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        p.state = ProcessState.TERMINATED

    return gantt, procs
