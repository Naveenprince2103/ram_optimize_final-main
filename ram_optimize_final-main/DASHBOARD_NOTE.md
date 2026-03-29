# Dashboard Usage Note

## ⚠️ Important: Starting the Optimizer

Due to Playwright threading limitations, the **"Start Optimizer" button in the dashboard may cause errors**.

### ✅ Recommended Approach:

**Start the optimizer separately** before using the dashboard:

1. **Open a terminal** and run:
   ```bash
   python -m ram_sentinel optimize --auto
   ```

2. **Then start the dashboard** in another terminal:
   ```bash
   python start_dashboard.py
   ```

3. The dashboard will now show your tabs and monitor everything!

### 📊 What the Dashboard Does:

- **Monitor** - View real-time stats (always works)
- **Control Vault** - Mount/unmount (works from dashboard)
- **View Tabs** - See monitored tabs (works when optimizer is running separately)

### 🔧 Alternative: Use the Tray App

The **system tray app** doesn't have this threading issue:

```bash
python start_tray.py
```

Right-click the tray icon to start/stop the optimizer safely.

---

**The dashboard is best for monitoring, the tray app is best for control!** 🎯
