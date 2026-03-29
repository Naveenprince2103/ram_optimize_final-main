# Ghost Drive - Easy Mount/Unmount Guide

## 🚀 Easy Way to Use Ghost Drive

I've created simple shortcuts for you!

### **To Mount (Create R: Drive):**

**Just double-click:** `mount_ghost_drive.bat`

- Windows will ask for admin permission (click "Yes")
- R: drive appears automatically
- No need to open PowerShell manually!

### **To Unmount (Remove R: Drive):**

**Just double-click:** `unmount_ghost_drive.bat`

- Windows will ask for admin permission (click "Yes")
- R: drive disappears
- All data permanently deleted

---

## ❓ Why Admin Permission is Required

**Windows Security:**
- Creating drives = System-level operation
- Requires Administrator privileges
- This is a Windows restriction, not RAM Sentinel

**You'll see this prompt:**
```
User Account Control
Do you want to allow this app to make changes to your device?
[Yes] [No]
```

**Just click "Yes"** and it works!

---

## 💡 Make It Even Easier

### **Option 1: Keep PowerShell Open**

1. Open PowerShell as Administrator **once**
2. Keep it open all day
3. Mount/unmount whenever you want
4. No repeated prompts!

```powershell
# In the admin PowerShell:
cd f:\veri\ram_project_1

# Mount
python -m ram_sentinel vault --mount --size 500M --mount-point R:

# Use R: drive...

# Unmount
python -m ram_sentinel vault --unmount --mount-point R:
```

### **Option 2: Use the .bat Files**

- `mount_ghost_drive.bat` - Double-click to mount
- `unmount_ghost_drive.bat` - Double-click to unmount
- Click "Yes" when Windows asks for permission

---

## 🎯 Typical Workflow

**Morning:**
1. Double-click `mount_ghost_drive.bat`
2. Click "Yes" for admin
3. Use R: drive all day

**Evening:**
1. Double-click `unmount_ghost_drive.bat`
2. Click "Yes" for admin
3. All data destroyed, RAM freed

---

## 🔒 Security Note

**Why this is actually GOOD:**
- Admin requirement = Extra security layer
- Prevents malware from creating drives
- You control when drives are created/destroyed

---

## 📝 Summary

**Yes, you need admin privileges each time**, but now you have:

✅ **Easy shortcuts** - Just double-click .bat files
✅ **Auto-prompt** - Windows asks for permission automatically
✅ **No manual PowerShell** - Everything automated

**Just double-click and click "Yes"!** 🎯
