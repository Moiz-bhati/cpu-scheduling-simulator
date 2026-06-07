"""
Round Robin Scheduling Algorithm (Preemptive)
Each process gets a fixed time quantum; interrupted processes re-enter ready queue.
"""

import copy
from collections import deque
from typing import List, Tuple
from models.process import Process, ProcessState


def round_robin(processes: List[Process], quantum: int = 2) -> Tuple[List[dict], List[Process]]:
    procs = [copy.deepcopy(p) for p in processes]
    for p in procs:
        p.remaining_time = p.burst_time

    procs_sorted = sorted(procs, key=lambda p: (p.arrival_time, p.pid))
    n = len(procs_sorted)

    gantt = []
    current_time = 0
    queue = deque()
    response_set = set()
    completed = 0
    idx = 0  # index into sorted arrival list

    # Enqueue processes that arrive at time 0
    while idx < n and procs_sorted[idx].arrival_time <= current_time:
        queue.append(procs_sorted[idx])
        idx += 1

    while completed < n:
        if not queue:
            current_time = procs_sorted[idx].arrival_time
            while idx < n and procs_sorted[idx].arrival_time <= current_time:
                queue.append(procs_sorted[idx])
                idx += 1

        proc = queue.popleft()

        if proc.pid not in response_set:
            proc.response_time = current_time - proc.arrival_time
            proc.start_time = current_time
            response_set.add(proc.pid)

        exec_time = min(quantum, proc.remaining_time)
        gantt.append({"pid": proc.pid, "start": current_time, "end": current_time + exec_time})
        current_time += exec_time
        proc.remaining_time -= exec_time

        # Enqueue newly arrived processes
        while idx < n and procs_sorted[idx].arrival_time <= current_time:
            queue.append(procs_sorted[idx])
            idx += 1

        if proc.remaining_time == 0:
            proc.completion_time = current_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.state = ProcessState.TERMINATED
            completed += 1
        else:
            queue.append(proc)

    return gantt, procs_sorted
