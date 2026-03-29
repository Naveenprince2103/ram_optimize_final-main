# Process Monitor - Quick Guide

## 📊 Monitor All System Processes

RAM Sentinel now includes a **Process Monitor** that tracks ALL running programs on your computer, not just browser tabs!

---

## 🚀 How to Use

### **From the System Tray:**

Right-click the RAM Sentinel tray icon and select:

1. **📊 Process Monitor** - View top 10 RAM-consuming processes
2. **📄 Generate RAM Report** - Save detailed report to file

---

## 📋 What You'll See

### **Process Monitor View:**
```
RAM USAGE MONITOR
System RAM: 8.5GB / 16.0GB (53.1%)

Top 10 Processes:
PID      Memory (MB)  Name
--------------------------------------------------
1234     1024.5       chrome.exe
5678     856.2        python.exe
9012     512.8        code.exe
...
```

### **RAM Report (Saved File):**
```
============================================================
RAM SENTINEL - PROCESS MONITOR REPORT
============================================================
Generated: 2026-01-24 18:15:30

SYSTEM RAM USAGE:
  Total:     16.00 GB
  Used:      8.50 GB (53.1%)
  Available: 7.50 GB

TOP 15 PROCESSES BY RAM USAGE:
PID      Memory (MB)  CPU %    Name
------------------------------------------------------------
1234     1024.5       2.5      chrome.exe
5678     856.2        0.1      python.exe
...
============================================================
```

Reports are saved to:
```
~/Documents/RAM_Sentinel_Reports/ram_report_YYYYMMDD_HHMMSS.txt
```

---

## 🎯 Use Cases

### **Find RAM Hogs:**
Quickly identify which programs are using the most memory.

### **Performance Troubleshooting:**
See what's slowing down your system.

### **Before/After Comparison:**
Generate reports before and after optimization to see improvements.

### **System Monitoring:**
Track RAM usage over time by generating periodic reports.

---

## ⚙️ Configuration

Edit `ram_sentinel/core/process_monitor.py` to customize:

```python
self.threshold_mb = 500  # Alert threshold (default: 500MB)
```

---

## 🔧 Advanced: Kill Processes (Coming Soon)

Future versions will allow you to:
- Kill RAM-hogging processes from the tray menu
- Set automatic kill rules for specific programs
- Whitelist critical processes

---

## 📝 Notes

- **Requires no admin privileges** to view processes
- **Real-time data** - always shows current state
- **Cross-platform** - works on Windows, Linux, macOS
- **Lightweight** - minimal performance impact

---

**Monitor everything, optimize intelligently!** 🎯
