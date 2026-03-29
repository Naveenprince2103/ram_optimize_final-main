# 🛡️ RAM Sentinel

**Intelligent RAM Optimization & Secure Volatile Storage**

RAM Sentinel is a powerful cross-platform tool that helps you optimize RAM usage and create secure volatile storage drives.

---

## ✨ Features

### 🌐 Neural Tab-Purger
- Automatically monitors browser tabs
- Closes inactive tabs to free RAM
- Saves closed tabs to "Read-Later" list
- Configurable inactivity threshold

### 💿 Ghost Drive
- Create ultra-fast RAM-only drives
- Data disappears on shutdown (by design)
- Perfect for temporary sensitive files
- Emergency panic wipe

### 📊 Process Monitor
- Track all system processes in real-time
- Identify RAM hogs
- Generate detailed reports
- Top 15 processes by memory usage

### 🌐 Web Dashboard
- Beautiful real-time monitoring interface
- Auto-refreshes every 3 seconds
- Control optimizer and vault from browser
- Professional grey theme

### 🎛️ System Tray App
- Run in background
- Easy access from taskbar
- Start/stop optimizer
- Mount/unmount vault

### 🚨 Emergency Panic
- Instant data destruction
- Closes all tabs
- Destroys vault data
- One-click emergency wipe

### 🛡️ 100% Offline (Privacy First)
- **Zero Telemetry**: No servers, no tracking, no "cloud sync".
- **Works Anywhere**: Use it on a plane, air-gapped PC, or without Wi-Fi.
- **Security**: Your monitoring data stays on your machine, period.

---

## 🚀 Quick Start

### Windows

1. **Install Python 3.13** from [python.org](https://www.python.org/downloads/)
2. **Extract this folder** to any location
3. **Double-click:** `setup.bat`
4. **Launch:**
   - Dashboard: `start_dashboard.bat`
   - Tray App: `start_ram_sentinel.bat`

### Linux/Mac

```bash
pip install -r requirements.txt
python -m playwright install chromium
python start_dashboard.py
```

---

## 📋 System Requirements

- **OS:** Windows 10/11, Linux, or macOS
- **Python:** 3.10 or higher
- **RAM:** 4GB minimum (8GB+ recommended)
- **Optional:** ImDisk Toolkit (Windows, for Ghost Drive)

---

## 📚 Documentation

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Complete feature guide
- **[DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)** - Web dashboard guide
- **[TRAY_APP_GUIDE.md](TRAY_APP_GUIDE.md)** - System tray guide
- **[PROCESS_MONITOR_GUIDE.md](PROCESS_MONITOR_GUIDE.md)** - Process monitoring
- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation
- **[DISTRIBUTION.md](DISTRIBUTION.md)** - How to share this tool

---

## 🎯 Usage Examples

### Start the Dashboard
```bash
python start_dashboard.py
# Opens at http://127.0.0.1:5000
```

### Start Tab Optimizer
```bash
python -m ram_sentinel optimize --auto
```

### Mount Ghost Drive (Windows)
```bash
python -m ram_sentinel vault --mount --size 500M --mount-point R:
```

### Emergency Panic
```bash
python -m ram_sentinel panic
```

---

## ⚙️ Configuration

Edit `ram_sentinel/core/config.py`:

```python
MAX_TAB_AGE_MINUTES = 60           # Max tab age
INACTIVE_THRESHOLD_MINUTES = 30    # Inactivity timeout
DEFAULT_VAULT_SIZE = "500M"        # RAM drive size
```

---

## 🔒 Security & Privacy

- **No telemetry** - Zero data collection
- **No internet required** - Works offline after setup
- **Volatile storage** - Data disappears by design
- **No logs to disk** - Console output only
- **Open source** - Review the code yourself

---

## ⚠️ Important Warnings

### Ghost Drive
- ❌ Data is **permanently lost** on shutdown/crash
- ❌ No backup or recovery possible
- ❌ Not for important files
- ✅ Perfect for temporary sensitive data

### Swap/Hibernation
- Disable swap/pagefile for true RAM-only security
- See USAGE_GUIDE.md for instructions

---

## 🆘 Troubleshooting

### "Python not found"
Install Python 3.13 from python.org

### "No module named 'flask'"
Run: `pip install -r requirements.txt`

### "Playwright browser not found"
Run: `python -m playwright install chromium`

### "ImDisk not found" (Windows)
Download from: https://sourceforge.net/projects/imdisk-toolkit/

---

## 📦 What's Included

```
ram_project_1/
├── ram_sentinel/          # Main application code
├── website/               # Landing page
├── setup.bat             # Auto-installer (Windows)
├── start_dashboard.bat   # Dashboard launcher
├── start_ram_sentinel.bat # Tray app launcher
├── requirements.txt      # Python dependencies
└── *.md files            # Documentation
```

---

## 🌐 Distribution

Want to share RAM Sentinel with others?

1. **Create ZIP** of this entire folder
2. **Upload** to Google Drive, GitHub, or cloud storage
3. **Share link** with installation instructions

See **[DISTRIBUTION.md](DISTRIBUTION.md)** for detailed options including:
- Hosting a website (GitHub Pages, Netlify)
- Creating downloadable packages
- Setting up auto-updates

---

## 📄 License

Free & Open Source Software

Provided as-is for educational and personal use.

---

## 🤝 Contributing

RAM Sentinel is designed to be extensible:
- New vault backends
- Additional browser support
- Platform-specific optimizations
- Security enhancements

---

## 🎉 Credits

Built for privacy-conscious users who value performance and security.

---

**RAM Sentinel** - Intelligent RAM optimization and secure volatile storage for privacy-conscious users.

🛡️ **Protect your RAM. Protect your privacy.**
# ram_optimize_final
