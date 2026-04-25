from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

PROCESS_STATES = ("NEW", "READY", "RUNNING", "WAITING", "TERMINATED")


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    remaining_time: int = field(init=False)
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    state: str = field(init=False, default="NEW")

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time

    @property
    def turnaround_time(self) -> int:
        if self.completion_time is None:
            return 0
        return self.completion_time - self.arrival_time

    @property
    def waiting_time(self) -> int:
        return self.turnaround_time - self.burst_time


@dataclass
class LifecycleEvent:
    timestamp: float
    pid: str
    state: str
    message: str
    algorithm: str


@dataclass
class ScheduleResult:
    algorithm_name: str
    processes: List[Process]
    timeline: List[Tuple[int, int, str]]
    total_time: int
    cpu_utilization: float
    average_turnaround: float
    average_waiting: float
    context_switches: int


class ProcessLifecycleAnalyzer:
    def __init__(self) -> None:
        self.events: List[LifecycleEvent] = []

    def record(self, timestamp: float, process: Process, state: str, message: str = "", algorithm: str = "Capture") -> None:
        process.state = state
        self.events.append(
            LifecycleEvent(timestamp=timestamp, pid=process.pid, state=state, message=message, algorithm=algorithm)
        )

    def print_log(self) -> None:
        print("\n=== Process Lifecycle Events ===")
        for event in sorted(self.events, key=lambda e: (e.timestamp, e.algorithm, e.pid)):
            time_str = f"{event.timestamp:.1f}s"
            print(
                f"[{time_str}] {event.algorithm:<12} PID={event.pid:>3} STATE={event.state:>10} {event.message}"
            )


class SchedulerSimulator:
    def __init__(self, processes: List[Process], analyzer: ProcessLifecycleAnalyzer, verbose: bool = False) -> None:
        self.original_processes = processes
        self.analyzer = analyzer
        self.verbose = verbose

    def _clone_processes(self) -> List[Process]:
        return [Process(pid=p.pid, arrival_time=p.arrival_time, burst_time=p.burst_time) for p in self.original_processes]

    def simulate_fcfs(self) -> ScheduleResult:
        processes = self._clone_processes()
        current_time = 0
        timeline: List[Tuple[int, int, str]] = []
        ready_queue: List[Process] = []
        remaining = sorted(processes, key=lambda p: p.arrival_time)
        context_switches = 0

        while remaining or ready_queue:
            while remaining and remaining[0].arrival_time <= current_time:
                proc = remaining.pop(0)
                self.analyzer.record(current_time, proc, "READY", "Arrived and ready", algorithm="FCFS")
                ready_queue.append(proc)
                if self.verbose:
                    print(f"[FCFS] t={current_time} -> {proc.pid} entered READY")

            if not ready_queue:
                if remaining:
                    current_time = remaining[0].arrival_time
                    continue
                break

            proc = ready_queue.pop(0)
            if proc.start_time is None:
                proc.start_time = current_time
            self.analyzer.record(current_time, proc, "RUNNING", "Started execution", algorithm="FCFS")
            if self.verbose:
                print(f"[FCFS] t={current_time} -> {proc.pid} is RUNNING")

            timeline.append((current_time, current_time + proc.burst_time, proc.pid))
            context_switches += 1 if timeline and len(timeline) > 1 else 0
            current_time += proc.burst_time
            proc.remaining_time = 0
            proc.completion_time = current_time
            self.analyzer.record(current_time, proc, "TERMINATED", "Process completed", algorithm="FCFS")
            if self.verbose:
                print(f"[FCFS] t={current_time} -> {proc.pid} TERMINATED")

        return self._build_result("FCFS", processes, timeline, current_time, context_switches)

    def simulate_sjf(self) -> ScheduleResult:
        processes = self._clone_processes()
        current_time = 0
        timeline: List[Tuple[int, int, str]] = []
        ready_queue: List[Process] = []
        remaining = sorted(processes, key=lambda p: p.arrival_time)
        context_switches = 0

        while remaining or ready_queue:
            while remaining and remaining[0].arrival_time <= current_time:
                proc = remaining.pop(0)
                self.analyzer.record(current_time, proc, "READY", "Arrived and ready", algorithm="SJF")
                ready_queue.append(proc)
                if self.verbose:
                    print(f"[SJF] t={current_time} -> {proc.pid} entered READY")

            if not ready_queue:
                if remaining:
                    current_time = remaining[0].arrival_time
                    continue
                break

            ready_queue.sort(key=lambda p: p.burst_time)
            proc = ready_queue.pop(0)
            if proc.start_time is None:
                proc.start_time = current_time
            self.analyzer.record(current_time, proc, "RUNNING", "Started execution", algorithm="SJF")
            if self.verbose:
                print(f"[SJF] t={current_time} -> {proc.pid} is RUNNING")

            timeline.append((current_time, current_time + proc.burst_time, proc.pid))
            context_switches += 1 if timeline and len(timeline) > 1 else 0
            current_time += proc.burst_time
            proc.remaining_time = 0
            proc.completion_time = current_time
            self.analyzer.record(current_time, proc, "TERMINATED", "Process completed", algorithm="SJF")
            if self.verbose:
                print(f"[SJF] t={current_time} -> {proc.pid} TERMINATED")

        return self._build_result("SJF", processes, timeline, current_time, context_switches)

    def simulate_round_robin(self, quantum: int) -> ScheduleResult:
        processes = self._clone_processes()
        current_time = 0
        timeline: List[Tuple[int, int, str]] = []
        ready_queue: List[Process] = []
        remaining = sorted(processes, key=lambda p: p.arrival_time)
        context_switches = 0

        while remaining or ready_queue:
            while remaining and remaining[0].arrival_time <= current_time:
                proc = remaining.pop(0)
                self.analyzer.record(current_time, proc, "READY", "Arrived and ready", algorithm="Round Robin")
                ready_queue.append(proc)
                if self.verbose:
                    print(f"[RR] t={current_time} -> {proc.pid} entered READY")

            if not ready_queue:
                if remaining:
                    current_time = remaining[0].arrival_time
                    continue
                break

            proc = ready_queue.pop(0)
            if proc.start_time is None:
                proc.start_time = current_time
            self.analyzer.record(current_time, proc, "RUNNING", "Began quantum", algorithm="Round Robin")
            if self.verbose:
                print(f"[RR] t={current_time} -> {proc.pid} is RUNNING with {proc.remaining_time} remaining")

            run_time = min(quantum, proc.remaining_time)
            timeline.append((current_time, current_time + run_time, proc.pid))
            context_switches += 1 if timeline and len(timeline) > 1 else 0
            current_time += run_time
            proc.remaining_time -= run_time

            if proc.remaining_time == 0:
                proc.completion_time = current_time
                self.analyzer.record(current_time, proc, "TERMINATED", "Process completed", algorithm="Round Robin")
                if self.verbose:
                    print(f"[RR] t={current_time} -> {proc.pid} TERMINATED")
            else:
                self.analyzer.record(current_time, proc, "WAITING", "Quantum ended, waiting for next turn", algorithm="Round Robin")
                if self.verbose:
                    print(f"[RR] t={current_time} -> {proc.pid} returning to READY with {proc.remaining_time} remaining")
                while remaining and remaining[0].arrival_time <= current_time:
                    next_proc = remaining.pop(0)
                    self.analyzer.record(current_time, next_proc, "READY", "Arrived and ready", algorithm="Round Robin")
                    ready_queue.append(next_proc)
                ready_queue.append(proc)

        return self._build_result("Round Robin", processes, timeline, current_time, context_switches)

    def _build_result(self, name: str, processes: List[Process], timeline: List[Tuple[int, int, str]], total_time: int, context_switches: int) -> ScheduleResult:
        total_burst = sum(p.burst_time for p in processes)
        average_turnaround = sum(p.turnaround_time for p in processes) / len(processes)
        average_waiting = sum(p.waiting_time for p in processes) / len(processes)
        utilization = 100.0 * total_burst / total_time if total_time else 0.0
        return ScheduleResult(
            algorithm_name=name,
            processes=processes,
            timeline=timeline,
            total_time=total_time,
            cpu_utilization=utilization,
            average_turnaround=average_turnaround,
            average_waiting=average_waiting,
            context_switches=context_switches,
        )


def generate_workload(count: int, max_arrival: int, burst_range: Tuple[int, int], seed: Optional[int] = None) -> List[Process]:
    if seed is not None:
        random.seed(seed)

    processes: List[Process] = []
    for pid in range(1, count + 1):
        arrival_time = random.randint(0, max_arrival)
        burst_time = random.randint(burst_range[0], burst_range[1])
        processes.append(Process(pid=f"P{pid}", arrival_time=arrival_time, burst_time=burst_time))

    return sorted(processes, key=lambda p: (p.arrival_time, p.pid))


def print_workload(processes: List[Process]) -> None:
    print("\n=== Observed Workload ===")
    print(f"{'PID':<5}{'Arrival':<10}{'Burst':<8}")
    for proc in processes:
        print(f"{proc.pid:<5}{proc.arrival_time:<10}{proc.burst_time:<8}")


def print_result(result: ScheduleResult) -> None:
    print(f"\n--- {result.algorithm_name} Scheduling Summary ---")
    print(f"Makespan: {result.total_time} units")
    print(f"CPU Utilization: {result.cpu_utilization:.1f}%")
    print(f"Average Turnaround Time: {result.average_turnaround:.2f}")
    print(f"Average Waiting Time: {result.average_waiting:.2f}")
    print(f"Context Switches: {result.context_switches}")
    print("\nProcess details:")
    print(f"{'PID':<5}{'Arrival':<10}{'Burst':<8}{'Start':<8}{'Complete':<10}{'Turnaround':<12}{'Waiting':<8}")
    for proc in sorted(result.processes, key=lambda p: p.pid):
        print(
            f"{proc.pid:<5}{proc.arrival_time:<10}{proc.burst_time:<8}"
            f"{proc.start_time or 0:<8}{proc.completion_time or 0:<10}"
            f"{proc.turnaround_time:<12}{proc.waiting_time:<8}"
        )
    print_gantt_chart(result)


def print_gantt_chart(result: ScheduleResult) -> None:
    print("\nGantt chart:")
    if not result.timeline:
        print("No schedule available.")
        return

    bars = []
    for start, end, pid in result.timeline:
        bars.append(f"[{start:>2}-{end:<2}] {pid}")
    print(" -> ".join(bars))


def compare_results(results: List[ScheduleResult]) -> None:
    print("\n=== Scheduler Comparison ===")
    print(f"{'Algorithm':<15}{'Turnaround':<15}{'Waiting':<12}{'Utilization':<14}{'Context Switches':<18}")
    for result in results:
        print(
            f"{result.algorithm_name:<15}"
            f"{result.average_turnaround:<15.2f}"
            f"{result.average_waiting:<12.2f}"
            f"{result.cpu_utilization:<14.1f}"
            f"{result.context_switches:<18}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process Lifecycle Analyzer & Scheduler Simulator")
    parser.add_argument("--processes", type=int, default=8, help="Number of processes to generate")
    parser.add_argument("--max-arrival", type=int, default=10, help="Maximum arrival time for workloads")
    parser.add_argument("--burst-min", type=int, default=2, help="Minimum burst length")
    parser.add_argument("--burst-max", type=int, default=10, help="Maximum burst length")
    parser.add_argument("--quantum", type=int, default=4, help="Quantum size for Round Robin")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible workloads")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed scheduling event output")
    parser.add_argument("--speed", type=float, default=4.0, help="Simulation speed multiplier for real-time capture")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    processes = generate_workload(args.processes, args.max_arrival, (args.burst_min, args.burst_max), args.seed)

    print("Process Lifecycle Analyzer & Scheduler Simulator")
    print("Theme: Process Management & CPU Scheduling")
    print_workload(processes)

    analyzer = ProcessLifecycleAnalyzer()
    simulator = SchedulerSimulator(processes, analyzer, verbose=args.verbose)

    print("\n=== Real-time capture started ===")
    start_time = time.time()
    for proc in processes:
        simulated_event_time = start_time + proc.arrival_time / args.speed
        delay = max(0.0, simulated_event_time - time.time())
        time.sleep(delay)
        elapsed = time.time() - start_time
        analyzer.record(elapsed, proc, "NEW", "Process created and observed")
        print(f"[{elapsed:.1f}s] Observed {proc.pid} creation, arrival={proc.arrival_time}, burst={proc.burst_time}")

    print("=== Real-time capture complete ===")

    results = [
        simulator.simulate_fcfs(),
        simulator.simulate_sjf(),
        simulator.simulate_round_robin(args.quantum),
    ]

    analyzer.print_log()
    for result in results:
        print_result(result)
    compare_results(results)


if __name__ == "__main__":
    main()
