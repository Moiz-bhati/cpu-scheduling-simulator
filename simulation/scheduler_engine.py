"""
Scheduler Engine
Drives the step-by-step simulation, exposes state for GUI consumption.
"""

from typing import List, Optional, Callable
from models.process import Process, ProcessState, PROCESS_COLORS
from algorithms import fcfs, sjf, srtf, round_robin, priority_scheduling, preemptive_priority, multilevel_queue


ALGORITHM_MAP = {
    "FCFS": fcfs,
    "SJF": sjf,
    "SRTF": srtf,
    "Priority": priority_scheduling,
    "Preemptive Priority": preemptive_priority,
    "Round Robin": round_robin,
    "Multilevel Queue": multilevel_queue,
}


class SchedulerEngine:
    def __init__(self):
        self.processes: List[Process] = []
        self.algorithm: str = "FCFS"
        self.quantum: int = 2
        self.gantt: List[dict] = []
        self.result_procs: List[Process] = []
        self.current_step: int = 0
        self.total_steps: int = 0
        self._color_map: dict = {}

    def set_processes(self, processes: List[Process]):
        self.processes = processes
        self._assign_colors()

    def _assign_colors(self):
        for i, p in enumerate(self.processes):
            self.color_map_assign(p.pid, i)

    def color_map_assign(self, pid: str, index: int):
        self._color_map[pid] = PROCESS_COLORS[index % len(PROCESS_COLORS)]

    def get_color(self, pid: str) -> str:
        return self._color_map.get(pid, "#3498DB")

    def run(self):
        """Execute the selected algorithm and store full results."""
        if not self.processes:
            return

        algo_fn = ALGORITHM_MAP.get(self.algorithm, fcfs)

        if self.algorithm in ("Round Robin", "Multilevel Queue"):
            self.gantt, self.result_procs = algo_fn(self.processes, self.quantum)
        else:
            self.gantt, self.result_procs = algo_fn(self.processes)

        # Assign colors to result procs
        pid_to_result = {p.pid: p for p in self.result_procs}
        for i, p in enumerate(self.processes):
            self._color_map[p.pid] = PROCESS_COLORS[i % len(PROCESS_COLORS)]

        self.total_steps = len(self.gantt)
        self.current_step = 0

    def get_step_state(self, step: int) -> dict:
        """Return simulation state at a given Gantt step index."""
        if step >= len(self.gantt):
            return {}

        current_block = self.gantt[step]
        current_time = current_block["start"]
        running_pid = current_block["pid"]

        # Determine ready queue: arrived but not yet completed and not currently running
        completed_pids = set()
        for i, block in enumerate(self.gantt):
            if i < step and block["end"] <= current_time:
                # Check if fully done
                pass

        # Build state for each process
        proc_states = {}
        for p in self.result_procs:
            if p.arrival_time > current_time:
                proc_states[p.pid] = ProcessState.NEW
            elif p.pid == running_pid:
                proc_states[p.pid] = ProcessState.RUNNING
            elif p.completion_time is not None and p.completion_time <= current_time:
                proc_states[p.pid] = ProcessState.TERMINATED
            elif p.arrival_time <= current_time:
                proc_states[p.pid] = ProcessState.READY
            else:
                proc_states[p.pid] = ProcessState.NEW

        ready_queue = [pid for pid, state in proc_states.items() if state == ProcessState.READY]

        return {
            "step": step,
            "current_time": current_time,
            "running_pid": running_pid,
            "ready_queue": ready_queue,
            "proc_states": proc_states,
            "gantt_so_far": self.gantt[:step + 1],
        }

    def compute_metrics(self) -> dict:
        """Compute aggregate metrics from result processes."""
        if not self.result_procs:
            return {}

        n = len(self.result_procs)
        total_wt = sum(p.waiting_time or 0 for p in self.result_procs)
        total_tat = sum(p.turnaround_time or 0 for p in self.result_procs)
        total_rt = sum(p.response_time or 0 for p in self.result_procs)

        if self.gantt:
            total_span = self.gantt[-1]["end"] - self.gantt[0]["start"]
            total_cpu_busy = sum(b["end"] - b["start"] for b in self.gantt)
            cpu_util = (total_cpu_busy / total_span * 100) if total_span > 0 else 0
            throughput = n / total_span if total_span > 0 else 0
        else:
            cpu_util = 0
            throughput = 0

        return {
            "avg_waiting_time": total_wt / n,
            "avg_turnaround_time": total_tat / n,
            "avg_response_time": total_rt / n,
            "cpu_utilization": cpu_util,
            "throughput": throughput,
        }

    def run_all_algorithms(self) -> dict:
        """Run all algorithms and return comparative metrics."""
        results = {}
        algos = ["FCFS", "SJF", "SRTF", "Priority", "Preemptive Priority", "Round Robin"]

        for algo in algos:
            algo_fn = ALGORITHM_MAP[algo]
            try:
                if algo in ("Round Robin",):
                    gantt, result_procs = algo_fn(self.processes, self.quantum)
                else:
                    gantt, result_procs = algo_fn(self.processes)

                n = len(result_procs)
                if n == 0:
                    continue

                total_wt = sum(p.waiting_time or 0 for p in result_procs)
                total_tat = sum(p.turnaround_time or 0 for p in result_procs)
                total_rt = sum(p.response_time or 0 for p in result_procs)

                if gantt:
                    total_span = gantt[-1]["end"] - gantt[0]["start"]
                    total_cpu_busy = sum(b["end"] - b["start"] for b in gantt)
                    cpu_util = (total_cpu_busy / total_span * 100) if total_span > 0 else 0
                else:
                    cpu_util = 0

                results[algo] = {
                    "avg_waiting_time": total_wt / n,
                    "avg_turnaround_time": total_tat / n,
                    "avg_response_time": total_rt / n,
                    "cpu_utilization": cpu_util,
                }
            except Exception:
                pass

        return results
