# RAM Sentinel - System Tray Quick Start

## 🚀 New: Background Service with System Tray!

RAM Sentinel now includes a **system tray application** that runs in the background. No more command line needed!

### ✨ Features:
- **System tray icon** - Always accessible from your taskbar
- **Right-click menu** - Easy control of all features
- **Auto-start** - Optionally start with Windows
- **Background monitoring** - Tab Purger runs automatically
- **Quick panic button** - Emergency wipe from tray menu

---

## 📋 Quick Start

### 1. Start the Tray App

**Double-click:**
```
start_ram_sentinel.bat
```

Or run:
```bash
python start_tray.py
```

You'll see a **green/gray circle icon** in your system tray (near the clock).

### 2. Use the Tray Menu

**Right-click the tray icon** to see:
- **Start Optimizer** - Begin monitoring browser tabs
- **Stop Optimizer** - Stop monitoring
- **Mount Vault** - Create RAM drive
- **Unmount Vault** - Remove RAM drive
- **🚨 PANIC** - Emergency wipe everything
- **Status** - Show current state
- **Quit** - Exit the application

---

## 🔄 Auto-Start with Windows

To make RAM Sentinel start automatically when Windows boots:

```bash
python setup_autostart.py
```

Choose option **1** to enable auto-start.

This copies `start_ram_sentinel.bat` to your Windows Startup folder.

---

## 🎨 Tray Icon Colors

- **Gray** - Idle (nothing running)
- **Green** - Tab Optimizer active
- **Red** - Error state
- **Yellow** - Warning

---

## ⚙️ Configuration

Edit `ram_sentinel/core/config.py` to customize:
- Scan interval (default: 60 seconds)
- Inactivity threshold (default: 30 minutes)
- Vault size and mount point
- Read-Later directory

---

## 🆚 Tray App vs Command Line

### **Tray App (Recommended)**
✅ Runs in background
✅ Easy point-and-click control
✅ Auto-start with Windows
✅ Always accessible from taskbar
✅ No terminal needed

### **Command Line (Advanced)**
✅ More control over options
✅ Better for scripting
✅ Can see detailed logs
✅ Dry-run and testing modes

**Both work great!** Use whichever you prefer.

---

## 🛑 Stopping the Tray App

1. **Right-click** the tray icon
2. Click **Quit**

Or just close it from Task Manager if needed.

---

## 📝 Notes

- The tray app runs **headless** (no browser window)
- To connect to your Chrome, launch Chrome with `--remote-debugging-port=9222` first
- Logs still appear in console if you run from terminal
- Use `pythonw` instead of `python` to run without console window

---

**Enjoy hands-free RAM optimization!** 🎉
