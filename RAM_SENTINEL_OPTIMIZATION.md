# RAM Sentinel System Optimization and Logic

RAM Sentinel optimizes logic and system performance using a combination of clever algorithms and direct OS-level API integrations. Rather than just blindly terminating processes, it employs sophisticated behavioral analysis and resource manipulation.

Here is how RAM Sentinel technically achieves heavy optimization:

## 1. Advanced Memory Compaction (SystemOptimizer)
Instead of aggressively killing applications to save RAM, the system uses the native Windows API (`EmptyWorkingSet` via `ctypes.windll`) to perform memory compaction.

* **Logic:** It scans through running processes, opens a handle to each, and forces them to release unused or fragmented memory pages back to the OS.
* **Performance Impact:** Background applications stay alive but their RAM footprint is drastically reduced (often by tens or hundreds of megabytes per app) without losing user data or terminating the application entirely.

## 2. War Room / Game Mode (WarRoomManager)
The War Room activates a temporary max-performance state designed to dedicate all hardware cycles to a specific target (usually a game).

* **Service Suspension:** It temporarily stops notoriously heavy Windows background services like SysMain (Superfetch), WSearch (Disk Indexing), wuauserv (Updates), and DiagTrack (Telemetry).
* **Dynamic CPU Prioritization:** It loops through every background process (browsers, Discord, Spotify) and aggressively down-ranks their CPU priority to `IDLE_PRIORITY_CLASS`, while boosting your target game EXE to `HIGH_PRIORITY_CLASS`.

Once War Room is disengaged, it smoothly restores the exact priorities and services back to everyday operation.

## 3. Predictive Tab Purger (HPCE Engine)
Closing browser tabs blindly is frustrating for users, so RAM Sentinel implements a Human Presence Confidence Engine (HPCE).

* **Behavioral Fingerprinting:** It injects a tiny JavaScript tracker into your active tabs using Playwright. This tracks keystrokes, scrolling, and mouse movement. If you scroll heavily, you are flagged as a "Reader" (tab stays alive longer). If you type frequently, you are a "Creator" (tab is heavily protected).
* **Sigmoidal Idle Decay Curve:** It applies a mathematical curve `[P = 1 / (1 + e^(k * (t - t0)))]` to determine how fast a tab degrades in importance. The moment the calculated confidence drops below 5%, the tab is automatically purged from memory to save RAM, but its URL is saved to a ReadLaterStorage database so it can be restored with one click.

## 4. VRAM & Process Management
* **VRAM Monitoring:** It taps into Windows Management Instrumentation (WMI) to track GPU Video RAM usage—helping users identify graphic bottlenecks.
* **Secure Sandbox & Process Control:** If a process is leaking memory or acting erratically, RAM Sentinel can instantly suspend it (pausing its execution threads entirely without closing it) via its quarantine logic.

## How You Can Optimize Your Setup Further (Using RAM Sentinel):
* **Trigger Compaction Often:** Run `/api/optimizer/compact` (or press the compact button in the UI) before launching heavy workloads like Premiere Pro or AAA games.
* **Lean on the Purger:** Keep the tab purger running in the background. Because of the HPCE logic, you won't lose work on important tabs, but it will seamlessly harvest RAM from "Ghost" tabs you forgot about.
* **Use War Room Exclusively for Gaming:** Don't leave War Room on all the time, as it stalls important OS updates and indexing. Only toggle it directly prior to launching an intensive game.
