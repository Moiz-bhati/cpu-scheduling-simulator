"""
Process Model - Defines the Process data structure used throughout the scheduler.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"


# Color mapping for process states
STATE_COLORS = {
    ProcessState.NEW: "#9B59B6",
    ProcessState.READY: "#F39C12",
    ProcessState.RUNNING: "#27AE60",
    ProcessState.WAITING: "#E67E22",
    ProcessState.TERMINATED: "#3498DB",
}

# Predefined colors for process blocks in Gantt chart
PROCESS_COLORS = [
    "#3498DB", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6",
    "#1ABC9C", "#E67E22", "#ECF0F1", "#F1C40F", "#BDC3C7",
    "#16A085", "#8E44AD", "#2980B9", "#C0392B", "#27AE60",
]


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0
    queue_level: int = 0  # For multilevel queue

    # Computed during simulation
    completion_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None
    response_time: Optional[int] = None
    remaining_time: Optional[int] = None
    start_time: Optional[int] = None
    state: ProcessState = ProcessState.NEW
    color: str = "#3498DB"

    def reset(self):
        """Reset computed fields for re-simulation."""
        self.completion_time = None
        self.waiting_time = None
        self.turnaround_time = None
        self.response_time = None
        self.remaining_time = self.burst_time
        self.start_time = None
        self.state = ProcessState.NEW

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "queue_level": self.queue_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Process":
        return cls(
            pid=data["pid"],
            arrival_time=data["arrival_time"],
            burst_time=data["burst_time"],
            priority=data.get("priority", 0),
            queue_level=data.get("queue_level", 0),
        )
