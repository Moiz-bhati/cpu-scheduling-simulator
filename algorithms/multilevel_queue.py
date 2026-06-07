"""
Multilevel Queue Scheduling
Processes are assigned to queues based on queue_level.
Lower queue_level = higher queue priority.
Within each queue, Round Robin is used.
"""

import copy
from collections import deque
from typing import List, Tuple
from models.process import Process, ProcessState


def multilevel_queue(processes: List[Process], quantum: int = 2) -> Tuple[List[dict], List[Process]]:
    procs = [copy.deepcopy(p) for p in processes]
    for p in procs:
        p.remaining_time = p.burst_time

    # Determine queue levels
    levels = sorted(set(p.queue_level for p in procs))
    queues = {lvl: deque() for lvl in levels}

    n = len(procs)
    procs_sorted = sorted(procs, key=lambda p: (p.arrival_time, p.queue_level, p.pid))

    gantt = []
    current_time = 0
    completed = 0
    response_set = set()
    idx = 0

    def enqueue_arrived():
        nonlocal idx
        while idx < n and procs_sorted[idx].arrival_time <= current_time:
            p = procs_sorted[idx]
            queues[p.queue_level].append(p)
            idx += 1

    enqueue_arrived()

    while completed < n:
        # Find highest-priority non-empty queue
        selected_level = None
        for lvl in levels:
            if queues[lvl]:
                selected_level = lvl
                break

        if selected_level is None:
            if idx < n:
                current_time = procs_sorted[idx].arrival_time
                enqueue_arrived()
            continue

        proc = queues[selected_level].popleft()

        if proc.pid not in response_set:
            proc.response_time = current_time - proc.arrival_time
            proc.start_time = current_time
            response_set.add(proc.pid)

        exec_time = min(quantum, proc.remaining_time)
        gantt.append({"pid": proc.pid, "start": current_time, "end": current_time + exec_time})
        current_time += exec_time
        proc.remaining_time -= exec_time

        enqueue_arrived()

        if proc.remaining_time == 0:
            proc.completion_time = current_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.state = ProcessState.TERMINATED
            completed += 1
        else:
            queues[selected_level].append(proc)

    return gantt, procs
