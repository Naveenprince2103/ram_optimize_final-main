# 🛡️ RAM Sentinel: Deep-Dive Technical Blueprint & Architecture Report

This is a hyper-detailed architectural analysis of every corner of the RAM Sentinel project. It explores the exact programmatic mechanisms, logic flows, system hooks, and data-fetching methodologies that power each module.

---

## 1. 🌐 Neural Tab Purger (Browser DevTools API & Process Isolation)
**Core Function:** Analyzes active web browser tabs and dynamically shuts down background sub-processes that exceed idle thresholds, caching them for later to preserve RAM.

**Mechanisms (The "How"):**
Instead of forcefully terminating the entire browser executable (which creates a terrible user experience), this module targets the Chromium DevTools Protocol (CDP).
1. The purger script uses the `playwright.sync_api` to negotiate a WebSocket connection to Chrome running on `localhost` via the `--remote-debugging-port=9222` flag.
2. Once the WebSocket tunnel is established, it evaluates the `browser.contexts` array.
3. It maps through `context.pages()`, which returns every open tab as a programmable object.

**Fetching Telemetry (The "Data Extraction"):**
The module queries the Playwright CDP wrapper. It directly reads the `page.url` attribute and the `page.title()` attribute in real-time. If the URL does not belong to a whitelist (like YouTube/Spotify, which shouldn't be interrupted), it executes `page.close()`. The closed URL and Title string are then serialized using Python's `json.dump()` and appended to a persistent local flat-file (`read_later.json`).

---

## 2. 📊 Core System Profiler (Kernel Hooking via `psutil`)
**Core Function:** Calculates the machine's absolute top-level resource load, calculates CPU bottlenecks, and extracts a detailed per-process memory map.

**Mechanisms (The "How"):**
The dashboard needs data every 3 seconds. To prevent the monitoring tool itself from lagging the PC, data fetching is hyper-optimized.
The `psutil` library is not just a Python script; it is a compiled C-extension that binds directly to the underlying OS Kernel.

**Fetching Telemetry (The "Data Extraction"):**
*   **CPU Cycles:** It executes `psutil.cpu_percent(percpu=False, interval=0.1)`. This hooks into the Windows NT Kernel scheduling timers to see how many clock cycles were idle versus active over a 0.1-second interval.
*   **Memory Footprint:** The module loops over `psutil.process_iter()`. Instead of pulling everything (which is slow), it strictly queries `['pid', 'name', 'memory_info']`. 
*   **RSS (Resident Set Size):** The most crucial value fetched is `proc.info['memory_info'].rss`. Virtual Memory (VMS) is ignored because VMS includes data swapped to the hard drive. RSS accurately fetches *only* the bytes currently occupying physical silicon RAM, returning exact measurements mathematically divided by `(1024 * 1024)` to yield Megabytes.

---

## 3. 💿 Ghost Drive (ImDisk Virtual Space Mapping)
**Core Function:** Mounts a volatile volume that exists entirely inside physical RAM, ensuring forensic traces are destroyed instantly upon module unmounting or power failure.

**Mechanisms (The "How"):**
Windows NTFS does not natively support creating raw RAM disks out of the box. Therefore, this module leverages the `ImDisk` toolkit. 
When activated via the `vault_manager.py` script, Python utilizes the `subprocess` module to inject the command `imdisk -a -s 500M -m R: -p "/fs:ntfs /q /y"`. 
This bypasses the physical SSD sector allocation table and writes block data directly to physical memory addresses, formatting it instantaneously as NTFS for file compatibility.

**Fetching Telemetry (The "Data Extraction"):**
To monitor the health and storage capacity of the running RAM drive:
1. Python executes `shutil.disk_usage("R:\\")`, which fetches the low-level volume header parameters: `total`, `used`, and `free` bytes.
2. A recursive directory traversal (`os.walk("R:\\")`) is executed to sum up individual file metadata, grabbing `len(files)` to represent the total items stored securely inside the Ghost Drive.

---

## 4. 🗜️ Memory Compactor (Win32 `psapi` API DLL Hooks)
**Core Function:** Sweeps through all background processes and forcefully demands they return cached, unused memory pages back to the Operating System's standby list, clearing up massive amounts of RAM without shutting any apps down.

**Mechanisms (The "How"):**
Because this requires low-level pointer management, Python acts as a C-wrapper utilizing the `ctypes` library.
1. The script elevates itself using `ctypes.windll.shell32.IsUserAnAdmin()`.
2. It loops through all active process PIDs.
3. For each PID, it executes `ctypes.windll.kernel32.OpenProcess`, requesting `PROCESS_SET_QUOTA` and `PROCESS_QUERY_INFORMATION` privileges.

**Fetching Telemetry & Execution (The "Data Extraction"):**
Once a memory handle to the background application is obtained, the script calls `ctypes.windll.psapi.EmptyWorkingSet(handle)`. This is a raw Windows API command that commands the VMM (Virtual Memory Manager) to strip the working set of the target process down to its bare minimum required bytes. The script then fetches the difference in RSS memory (Before vs. After) to calculate the exact `freed_mb` returned to the user.

---

## 5. 🎮 VRAM Scanner (WMI Hardware Instrumentation)
**Core Function:** Maps out the GPU (Graphics Card) memory specifications to identify UI rendering bottlenecks outside of normal CPU/RAM boundaries.

**Mechanisms (The "How"):**
To communicate directly with motherboard and PCIe attached hardware, standard Python cannot simply read a file. It employs the `wmi` package.
The script initializes a Windows Management Instrumentation client `c = wmi.WMI()`.

**Fetching Telemetry (The "Data Extraction"):**
1. It queries the WMI SQL-like interface for `SELECT * FROM Win32_VideoController`.
2. For every GPU found, it extracts the string `Name` (e.g., "NVIDIA GeForce RTX 4070").
3. More importantly, it fetches the `AdapterRAM` property. This property is returned in raw bytes (often unsigned integers over 4 Billion). The script calculates `int(gpu.AdapterRAM) / (1024 ** 2)` to deliver the precise available VRAM layout shown on the dashboard.

---

## 6. 🧠 Neural Auto-Sandbox (Continuous Anomaly Evaluation)
**Core Function:** A Zero-Trust automated firewall for system memory. It quarantines unknown processes that exhibit rapid, hostile memory acquisition (characteristic of malware or severe memory leaks).

**Mechanisms (The "How"):**
1. A persistent daemon thread is spawned via `threading.Thread(target=self._monitor_loop)`. This completely detaches from the main dashboard, ensuring it never lags the UI.
2. It maintains a dictionary variable `history = {}` mapping `PID` -> `Memory (MB)`.
3. Every 3 seconds, it scans all processes. If a process name is NOT inside the `self.whitelist` array, it begins tracking its delta.

**Fetching Telemetry & Execution (The "Data Extraction"):**
If `mem_mb > 400` AND `mem_mb > history.get(pid) + 150`, the anomaly check fails. 
To immediately stop the hostile process without killing it (which allows users to review it), the script maps the PID to an OS object `psutil.Process(pid)` and executes `.suspend()`. This forcefully halts CPU time-slicing for the application's threads, achieving total isolation. When the user clears it, `.resume()` signals the OS kernel to re-allow CPU thread execution.

---

## 7. ⚔️ WAR ROOM (Subprocess SC Manipulation & Thread Priority)
**Core Function:** Repurposes the entire machine architecture into a highly-focused gaming or rendering environment. 

**Mechanisms (The "How"):**
The War Room triggers a synchronized sequence across two distinct vectors: Services and CPU Scheduling.

**Fetching Telemetry & Execution (The "Data Extraction"):**
1. **Service Halting:** It executes binary strings like `sc stop WSearch` and `sc stop Spooler`. It leverages `.stdout=subprocess.DEVNULL` to pipe command output into null space, executing system calls silently.
2. **CPU Target Locking:** It polls `psutil` to map every PID. It captures the existing priority variable (the `old_nice` value) of every app and saves it in memory. It then executes `proc.nice(0x00000040)`—forcing background apps to the lowest 'Idle' CPU priority ring. If a `target_game` is specified, it elevates that executable to `0x00000080` (High Priority), forcing the CPU to render the game before acknowledging background tasks. Upon shutdown, the original `old_nice` integers are restored perfectly to the state array.

---

## 8. 🌐 The Flask API & Dashboard Async Polling (Backend to Frontend)
**Core Function:** Acts as the display matrix taking backend Python hooks and visualizing them in real-time.

**Mechanisms (The "How"):**
The backend `server.py` implements a Flask Micro-WSGI framework. It bridges the gap between hardware (`psutil`) and the browser via REST API endpoints like `@app.route('/api/stats')`.

**Fetching Telemetry (The "Data Extraction"):**
The frontend HTML (`dashboard.html`) uses Vanilla JavaScript `fetch()` inside a `setInterval()` loop. Every 1.5 seconds, it pings the server for JSON payloads containing the CPU/RAM numbers. Moving the arrays into Chart.js elements, it splices `cpuData.push()` and dynamically recalculates the bezier curves on the fly, creating a fluid, hacker-style real-time response graphic.
