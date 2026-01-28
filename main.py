import pystray
from PIL import Image, ImageDraw
import threading
import sys
import os
import tkinter as tk

import config
import monitor
import uploader
import gui_settings
import json

def update_status_file(connected=False, monitoring=False, error=None, paused=False):
    status = {
        "connected": connected,
        "monitoring": monitoring,
        "paused": paused,
        "error": error,
        "pid": os.getpid()
    }
    try:
        with open("status.json", "w") as f:
            json.dump(status, f)
    except Exception:
        pass

class App:
    def __init__(self):
        self.monitor = None
        self.uploader = None
        self.icon = None
        self.config_data = config.load_config()
        self.is_paused = False
        self.connected = False
        # Init status as disconnected
        self.update_status()
        
        # Start command listener
        threading.Thread(target=self.command_loop, daemon=True).start()

    def update_status(self, error=None):
        monitoring = (self.monitor is not None)
        update_status_file(self.connected, monitoring, error, self.is_paused)

    def command_loop(self):
        import time
        while True:
            try:
                if os.path.exists("control.json"):
                    with open("control.json", "r") as f:
                        cmd = json.load(f)
                    os.remove("control.json") # Consume command
                    
                    if cmd.get("command") == "pause":
                        self.is_paused = True
                        if self.monitor: self.monitor.set_paused(True)
                        print("Paused via command.")
                    elif cmd.get("command") == "resume":
                        self.is_paused = False
                        if self.monitor: self.monitor.set_paused(False)
                        print("Resumed via command.")
                    
                    self.update_status()
            except Exception:
                pass
            time.sleep(0.5)

    def create_image(self):
        # Generate an image for the icon
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=(0, 0, 255))
        dc.rectangle((0, height // 2, width // 2, height), fill=(0, 255, 0))
        return image

    def start_sync(self, item=None):
        if self.monitor:
            self.stop_sync()
        
        # Reload config in case it changed
        self.config_data = config.load_config()
        cfg = config.get_active_profile(self.config_data)
        
        if not cfg or not cfg.get("local_path") or not cfg.get("server_host"):
            print("Config missing or invalid active profile, getting settings...")
            self.open_settings()
            return

        print(f"Starting sync service for profile: {cfg.get('name')}...")
        self.upl = uploader.Uploader(cfg["server_host"], cfg["server_port"], cfg["username"], cfg["remote_path"])
        
        # Test connection first
        if not self.upl.connect():
            print("Could not connect on startup")
            self.icon.notify("Connection Failed. Check Pageant/Settings.", "WinLinuxSync Error")
            self.update_status("Connection Failed")
            return
            
        self.monitor = monitor.Monitor(cfg["local_path"], self.upl, cfg.get("blacklist", []))
        self.monitor.start()
        
        if self.is_paused:
            self.monitor.set_paused(True)

        self.connected = True
        self.update_status()
        self.icon.notify(f"Connected to {cfg['server_host']}\nMonitoring {cfg['local_path']}", "WinLinuxSync Started")

    def stop_sync(self, item=None):
        if self.monitor:
            print("Stopping sync service...")
            self.monitor.stop()
            self.monitor = None
        if self.upl:
            self.upl.close()
            self.upl = None
        if self.upl:
            self.upl.close()
            self.upl = None
            
        self.connected = False
        self.update_status("Stopped")

    def on_config_saved(self, new_config):
        # This might not be called if running as subprocess, but keeping it logic-wise
        self.config_data = new_config
        self.start_sync()

    def open_settings(self, item=None):
        # Run settings in a separate process to avoid Tkinter/Thread freezes
        import subprocess
        print("Opening settings...")
        proc = subprocess.Popen([sys.executable, 'gui_settings.py'])
        
        # Start a thread to wait for it to close, then restart sync
        def wait_and_restart():
            proc.wait()
            print("Settings closed.")
            
            # Only restart sync if config is now valid
            current_config = config.load_config()
            active_p = config.get_active_profile(current_config)
            if active_p and active_p.get("local_path") and active_p.get("server_host"):
                print("Config valid, restarting sync...")
                self.start_sync()
            else:
                print("Config still missing or invalid. Sync not started.")
            
        threading.Thread(target=wait_and_restart, daemon=True).start()

    def exit_action(self, icon, item):
        self.stop_sync()
        icon.stop()

    def main(self):
        image = self.create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Start Sync', self.start_sync),
            pystray.MenuItem('Stop Sync', self.stop_sync),
            pystray.MenuItem('Settings', self.open_settings),
            pystray.MenuItem('Exit', self.exit_action)
        )
        self.icon = pystray.Icon("name", image, "WinLinuxSync", menu)
        
        # Auto-start if configured
        active_p = config.get_active_profile(self.config_data)
        if active_p and active_p.get("server_host"):
             # We want to start sync, but pystray blocks on run().
             # Schedule start after a brief delay or just call it? 
             # calling it directly is fine as long as monitor runs in thread (which it does).
             self.start_sync()

        # Always open settings on startup as requested
        self.open_settings()
             
        self.icon.run()

if __name__ == "__main__":
    app = App()
    app.main()
