import tkinter as tk
import psutil
import threading
import time
import os
import sys

# Ensure imports work from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class DynamicIsland:
    def __init__(self):
        self.root = tk.Tk()
        # Create a borderless, floating window
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='#0b0c15')
        
        # Position at top center of the screen
        screen_width = self.root.winfo_screenwidth()
        x = (screen_width // 2) - 150
        self.root.geometry(f'320x45+{x}+15')
        
        # Main Frame with neon cyber-border
        self.frame = tk.Frame(self.root, bg='#151621', highlightbackground='#00f2ff', highlightcolor='#00f2ff', highlightthickness=1)
        self.frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # SENTINEL Icon/Logo Indicator
        self.lbl_icon = tk.Label(self.frame, text="🛡️", bg='#151621', font=('Segoe UI Emoji', 12))
        self.lbl_icon.pack(side='left', padx=8)

        # CPU Monitor
        self.lbl_cpu = tk.Label(self.frame, text="CPU: 0%", fg='#ff0055', bg='#151621', font=('Consolas', 10, 'bold'))
        self.lbl_cpu.pack(side='left', padx=8)
        
        # RAM Monitor
        self.lbl_ram = tk.Label(self.frame, text="RAM: 0%", fg='#00f2ff', bg='#151621', font=('Consolas', 10, 'bold'))
        self.lbl_ram.pack(side='left', padx=8)
        
        # 1-Click Purge Button
        self.btn_purge = tk.Button(self.frame, text="PURGE", fg='#0b0c15', bg='#00f2ff', activebackground='#ffffff', 
                                   relief='flat', font=('Verdana', 8, 'bold'), cursor="hand2", command=self.trigger_purge)
        self.btn_purge.pack(side='right', padx=10, pady=5)
        
        # Make the widget draggable
        self.frame.bind('<Button-1>', self.click_window)
        self.frame.bind('<B1-Motion>', self.drag_window)
        # Double click to exit
        self.frame.bind('<Double-Button-1>', lambda e: self.root.destroy())
        
        # Start background health monitor loop
        self.running = True
        threading.Thread(target=self.update_stats_loop, daemon=True).start()

    def click_window(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f'+{x}+{y}')
        
    def trigger_purge(self):
        """Invoke the backend memory compaction script"""
        self.btn_purge.configure(text="CLEARING", bg='#ffc800')
        self.root.update()
        
        try:
            # We attempt to import and use the actual system optimizer script
            from ram_sentinel.core.system_optimizer import compact_memory
            res = compact_memory()
            freed = res.get('freed_mb', 0)
            print(f"Freed: {freed} MB")
            self.btn_purge.configure(text=f"OK! -{int(freed)}MB", bg='#00ff7f')
        except Exception as e:
            print("Purge error:", e)
            self.btn_purge.configure(text="ERROR", bg='#ff0055')
            
        # Reset button styling after 3 seconds
        self.root.after(3000, lambda: self.btn_purge.configure(text="PURGE", bg='#00f2ff'))

    def update_stats_loop(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                
                # Using root.after to safely update GUI from a background thread
                def update_labels(c=cpu, r=ram):
                    self.lbl_cpu.configure(text=f"CPU:{c:04.1f}%")
                    self.lbl_ram.configure(text=f"RAM:{r:04.1f}%")
                    
                    if c > 85: self.lbl_cpu.configure(fg='#ff0055')  # Danger Red
                    else: self.lbl_cpu.configure(fg='#ffffff')      # White
                        
                    if r > 85: self.lbl_ram.configure(fg='#ffc800')  # Warning Yellow
                    else: self.lbl_ram.configure(fg='#00f2ff')      # Cyber Blue
                        
                self.root.after(0, update_labels)
            except Exception:
                pass
            time.sleep(1)

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    DynamicIsland().run()
