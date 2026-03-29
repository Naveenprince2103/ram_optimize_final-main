# RAM Sentinel - Installation Guide

## 📦 Installing on Another Computer

### Method 1: Copy the Entire Folder (Easiest)

1. **Copy the entire `ram_project_1` folder** to the other laptop
2. **Install Python 3.13** (if not already installed)
3. **Install dependencies:**
   ```bash
   cd ram_project_1
   pip install -r requirements.txt
   python -m playwright install chromium
   ```
4. **Done!** You can now use RAM Sentinel

---

### Method 2: Share via ZIP File

1. **Compress the folder:**
   - Right-click `ram_project_1` folder
   - Select "Send to" → "Compressed (zipped) folder"

2. **Transfer the ZIP:**
   - USB drive
   - Email (if small enough)
   - Cloud storage (Google Drive, Dropbox, etc.)
   - Network share

3. **On the other laptop:**
   - Extract the ZIP file
   - Follow Method 1 steps 2-4

---

### Method 3: Git Repository (For Developers)

If you want to share updates easily:

1. **Create a Git repository:**
   ```bash
   cd ram_project_1
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Push to GitHub/GitLab:**
   - Create a repository on GitHub
   - Follow their instructions to push

3. **On other laptop:**
   ```bash
   git clone <your-repo-url>
   cd ram_project_1
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

---

## 🖥️ System Requirements

### All Computers Need:
- **Python 3.13** (or 3.10+)
- **Windows 10/11** (for Ghost Drive with ImDisk)
  - Or Linux/macOS (Ghost Drive uses tmpfs)
- **4GB+ RAM** (8GB+ recommended)
- **Internet connection** (for initial setup only)

### Windows-Specific:
- **ImDisk Toolkit** (for Ghost Drive feature)
  - Download: https://sourceforge.net/projects/imdisk-toolkit/

---

## 📋 Quick Setup on New Computer

### Step 1: Install Python
Download from: https://www.python.org/downloads/

### Step 2: Copy RAM Sentinel Folder
Transfer the `ram_project_1` folder

### Step 3: Install Dependencies
```bash
cd ram_project_1
pip install -r requirements.txt
python -m playwright install chromium
```

### Step 4: (Optional) Install ImDisk
For Ghost Drive feature on Windows:
https://sourceforge.net/projects/imdisk-toolkit/

### Step 5: Run!
```bash
# Dashboard
python start_dashboard.py

# Tray App
python start_tray.py

# Command Line
python -m ram_sentinel optimize --auto
```

---

## 🔧 What Gets Transferred

When you copy the folder, you get:

✅ **All Python code** - The entire RAM Sentinel application
✅ **Configuration files** - `requirements.txt`, `config.py`
✅ **Documentation** - All `.md` guide files
✅ **Launcher scripts** - `.bat` files for easy startup

❌ **Not included** - Python itself, Playwright browsers (must install)
❌ **Not included** - ImDisk Toolkit (Windows only, must install)

---

## 📁 Minimal Files Needed

If you only want the essentials:

```
ram_project_1/
├── ram_sentinel/          # Main code (REQUIRED)
├── requirements.txt       # Dependencies (REQUIRED)
├── start_dashboard.py     # Dashboard launcher
├── start_tray.py          # Tray app launcher
├── start_dashboard.bat    # Windows launcher
├── start_ram_sentinel.bat # Windows launcher
└── *.md files             # Documentation (optional but helpful)
```

---

## 🌐 Network Access to Dashboard

Want to access the dashboard from other devices on your network?

1. **On the computer running RAM Sentinel:**
   Edit `start_dashboard.py`:
   ```python
   run_server(host='0.0.0.0', port=5000)  # Allow network access
   ```

2. **Find your IP address:**
   ```bash
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```

3. **On other devices:**
   Open browser to: `http://YOUR_IP:5000`

---

## ⚠️ Important Notes

- **No installation needed** - It's a portable Python application
- **Each computer needs Python** - Can't run without it
- **Playwright browsers** - Must run `python -m playwright install chromium` on each computer
- **ImDisk** - Only needed for Ghost Drive feature on Windows
- **Read-Later data** - Stored in `~/Documents/RAM_Sentinel_ReadLater/` (not transferred)

---

## 🆘 Troubleshooting

### "Python not found"
Install Python 3.13 from python.org

### "No module named 'flask'"
Run: `pip install -r requirements.txt`

### "Playwright browser not found"
Run: `python -m playwright install chromium`

### "ImDisk not found" (Windows)
Install ImDisk Toolkit from SourceForge

---

**RAM Sentinel is fully portable - just copy and run!** 🚀
