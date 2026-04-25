# Process Lifecycle Analyzer & Scheduler Simulator

A Python-based learning tool for process management and CPU scheduling. It captures simulated process creation events in real time and compares three scheduling algorithms:

- First-Come First-Served (FCFS)
- Shortest Job First (SJF)
- Round Robin (RR)

## Features

- Real-time capture of process lifecycle events
- Simulator for FCFS, SJF, and Round Robin scheduling
- Metrics comparison for turnaround time, waiting time, CPU utilization, and context switching
- Gantt chart-like timeline output for each scheduling algorithm

## Run the simulator

```bash
python process_scheduler_simulator.py
```

### Optional arguments

- `--processes`: number of processes to generate (default: 8)
- `--max-arrival`: maximum arrival time for processes (default: 10)
- `--burst-min`: minimum burst duration (default: 2)
- `--burst-max`: maximum burst duration (default: 10)
- `--quantum`: time quantum for Round Robin (default: 4)
- `--seed`: random seed for repeatable workloads (default: 42)
- `--verbose`: print detailed scheduling events
- `--speed`: simulation speed multiplier for real-time capture (default: 4.0)

## Example

```bash
python process_scheduler_simulator.py --processes 10 --quantum 3 --verbose
```

This tool is designed for students to understand how scheduling decisions affect performance in terms of turnaround time, waiting time, and CPU utilization.
