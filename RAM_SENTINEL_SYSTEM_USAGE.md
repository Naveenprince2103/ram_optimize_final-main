# RAM Sentinel System Usage Architecture

In RAM Sentinel, system usage data (RAM, CPU, running processes, etc.) is collected and presented through a 3-tier architecture using Python and Flask. Here is the step-by-step breakdown of how the system posts usage in this project:

## 1. Stats Collection (The Core Backend)
RAM Sentinel uses the cross-platform Python library **psutil** to hook directly into the operating system without needing external software.

Scripts in `ram_sentinel/core/` are explicitly designed for this.
* **ProcessMonitor** (in `process_monitor.py`): Gathers active processes, their PIDs, and memory usage footprints.
* **MemoryAnalyzer** (in `memory_analyzer.py`): Focuses on generating broad system and browser-specific metrics (like isolating Chrome tab memory).

## 2. The REST API Layer (Flask Server)
The data gathered by the backend scripts is routed through a central web application. The file `ram_sentinel/dashboard/server.py` creates a Flask app that exposes various endpoints returning structured JSON data. Some of these endpoints include:

* `/api/stats`: Serves a comprehensive cache with system metrics, active tabs, and top process consumption.
* `/api/cpu`: Returns total CPU utilization alongside per-core usage metrics.
* `/api/system`: Delivers real-time RAM usage strings (total vs. available vs. used).
* `/api/processes`: Returns the top N most memory-intensive applications active on the machine.

## 3. Frontend Dashboard Updates
The visual dashboard interface (`ram_sentinel/dashboard/templates/dashboard.html` alongside corresponding JS scripts) behaves as the client for this data. It runs JavaScript `fetch()` polling periodically on the aforementioned `/api/` endpoints to retrieve the newest usage JSON statistics. Once received, it manipulates the DOM elements to continuously update progress bars, text displays, and charts with virtually zero delay, presenting real-time system usage to the user.
