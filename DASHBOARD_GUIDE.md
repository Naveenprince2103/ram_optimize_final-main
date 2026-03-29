# Web Dashboard - Quick Start Guide

## 🌐 Real-Time Monitoring Dashboard

RAM Sentinel now includes a **beautiful web dashboard** that shows everything in real-time!

---

## 🚀 How to Start

### **Option 1: Double-Click (Easiest)**
```
start_dashboard.bat
```

### **Option 2: Command Line**
```bash
python start_dashboard.py
```

The dashboard will automatically open in your browser at:
```
http://127.0.0.1:5000
```

---

## 📊 Dashboard Features

### **System RAM Monitor**
- Real-time RAM usage (GB and %)
- Visual progress bar
- Updates every 3 seconds

### **Browser Tab Monitor**
- Live count of monitored tabs
- List of all open tabs
- Tab titles and URLs
- Optimizer status (Running/Stopped)

### **Process Monitor**
- Top 15 RAM-consuming processes
- Process names and memory usage (MB)
- Sorted by RAM consumption

### **Ghost Drive Status**
- Vault mounted/unmounted status
- Visual status indicators

### **Control Panel**
- ▶️ **Start Optimizer** - Begin tab monitoring
- ⏹️ **Stop Optimizer** - Stop tab monitoring
- 📁 **Mount Vault** - Create RAM drive
- 📤 **Unmount Vault** - Remove RAM drive

---

## 🎨 Dashboard Design

- **Gradient background** - Beautiful purple/blue gradient
- **Glass-morphism cards** - Modern frosted glass effect
- **Real-time updates** - Auto-refresh every 3 seconds
- **Responsive layout** - Works on all screen sizes
- **Live indicator** - Shows when data is updating

---

## 🔧 How It Works

### **Backend (Flask REST API)**
```
GET  /api/stats      - All statistics
GET  /api/system     - System RAM only
GET  /api/processes  - Top processes
GET  /api/tabs       - Monitored tabs
POST /api/control/optimizer/start  - Start optimizer
POST /api/control/optimizer/stop   - Stop optimizer
POST /api/control/vault/mount      - Mount vault
POST /api/control/vault/unmount    - Unmount vault
```

### **Frontend (HTML/CSS/JS)**
- Pure JavaScript (no frameworks needed)
- Fetch API for REST calls
- Auto-refresh with `setInterval()`
- Responsive grid layout

---

## 📝 Usage Examples

### **Monitor System While Working**
1. Start dashboard: `start_dashboard.bat`
2. Click "▶️ Start Optimizer" to begin tab monitoring
3. Watch real-time RAM usage and process list
4. Dashboard updates automatically every 3 seconds

### **Quick RAM Check**
1. Open dashboard
2. See instant RAM usage and top processes
3. No need to start optimizer - just view stats

### **Control Everything from Browser**
1. Start/stop tab optimizer
2. Mount/unmount vault
3. All from the web interface!

---

## 🛑 Stopping the Dashboard

Press **Ctrl+C** in the terminal where you started it.

Or just close the terminal window.

---

## ⚙️ Configuration

Edit `ram_sentinel/dashboard/server.py` to change:
```python
# Server settings
host='127.0.0.1'  # Change to '0.0.0.0' for network access
port=5000         # Change port if needed
```

Edit the HTML template to customize:
```
ram_sentinel/dashboard/templates/dashboard.html
```

---

## 🌐 Access from Other Devices

To access the dashboard from other computers on your network:

1. Edit `start_dashboard.py`:
   ```python
   run_server(host='0.0.0.0', port=5000)
   ```

2. Find your IP address:
   ```bash
   ipconfig  # Windows
   ```

3. Access from other device:
   ```
   http://YOUR_IP:5000
   ```

---

## 🎯 Tips

- **Keep it running** - Dashboard can run alongside tray app
- **Bookmark it** - Add `http://127.0.0.1:5000` to browser favorites
- **Multiple tabs** - Open dashboard in multiple browser tabs
- **Mobile friendly** - Responsive design works on phones/tablets

---

## 🐛 Troubleshooting

### "Address already in use"
Port 5000 is taken. Change port in `start_dashboard.py`:
```python
run_server(port=5001)
```

### "Cannot connect"
Make sure the dashboard server is running. Check terminal for errors.

### "No data showing"
Wait a few seconds for first update (3-second refresh interval).

---

**Enjoy your beautiful real-time dashboard!** 🎉
