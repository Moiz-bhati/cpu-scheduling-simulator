"""
SRTF - Shortest Remaining Time First (Preemptive SJF)
At each time unit, the process with shortest remaining time executes.
"""

import copy
from typing import List, Tuple
from models.process import Process, ProcessState


def srtf(processes: List[Process]) -> Tuple[List[dict], List[Process]]:
    procs = [copy.deepcopy(p) for p in processes]
    for p in procs:
        p.remaining_time = p.burst_time

    n = len(procs)
    current_time = 0
    completed = 0
    gantt_raw = []
    response_set = set()

    max_time = sum(p.burst_time for p in procs) + max(p.arrival_time for p in procs) + 1

    while completed < n:
        available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]
        if not available:
            current_time += 1
            continue

        selected = min(available, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

        if selected.pid not in response_set:
            selected.response_time = current_time - selected.arrival_time
            selected.start_time = current_time
            response_set.add(selected.pid)

        # Append to gantt (merge consecutive same-process entries)
        if gantt_raw and gantt_raw[-1]["pid"] == selected.pid:
            gantt_raw[-1]["end"] = current_time + 1
        else:
            gantt_raw.append({"pid": selected.pid, "start": current_time, "end": current_time + 1})

        selected.remaining_time -= 1
        current_time += 1

        if selected.remaining_time == 0:
            selected.completion_time = current_time
            selected.turnaround_time = selected.completion_time - selected.arrival_time
            selected.waiting_time = selected.turnaround_time - selected.burst_time
            selected.state = ProcessState.TERMINATED
            completed += 1

    return gantt_raw, procs
