import threading
import sys
import os
import json
import traceback

import config
import monitor
import uploader

def update_status_file(connected=False, monitoring=False, error=None, connecting=False):
    status = {
        "connected": connected,
        "monitoring": monitoring,
        "connecting": connecting,
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
        self.upl = None
        self.config_data = config.load_config()
        self.connected = False
        self.connecting = False
        self.running = True
        # Init status as disconnected
        self.update_status()
        
        # Redirect logs to file for GUI
        self.logfile = open("sync.log", "a", buffering=1)
        sys.stdout = self.logfile
        sys.stderr = self.logfile

    def update_status(self, error=None):
        monitoring = (self.monitor is not None)
        update_status_file(self.connected, monitoring, error, self.connecting)

    def command_loop(self):
        import time
        while self.running:
            try:
                if os.path.exists("control.json"):
                    with open("control.json", "r") as f:
                        cmd = json.load(f)
                    os.remove("control.json") # Consume command
                    
                    if cmd.get("command") == "reconnect":
                        print("Reconnect triggered via command.")
                        self.start_sync()
                    elif cmd.get("command") == "stop":
                        print("Stop triggered via command.")
                        self.stop_sync()
                    
            except Exception:
                traceback.print_exc()
            time.sleep(0.5)

    def start_sync(self):
        if self.monitor or self.upl:
            self.stop_sync()
        
        # Reload config in case it changed
        self.config_data = config.load_config()
        cfg = config.get_active_profile(self.config_data)
        
        if not cfg or not cfg.get("local_path") or not cfg.get("server_host"):
            print("Config missing or invalid active profile.")
            self.update_status("Config missing")
            return

        print(f"Starting sync service for profile: {cfg.get('name')}...")
        if not os.path.isdir(cfg["local_path"]):
            error = f"Local folder does not exist: {cfg['local_path']}"
            print(error)
            self.update_status(error)
            return

        try:
            self.connecting = True
            self.update_status()
            self.upl = uploader.Uploader(cfg["server_host"], cfg["server_port"], cfg["username"], cfg["remote_path"])

            # Test connection first
            if not self.upl.connect():
                self.stop_sync()
                self.update_status("Connection Failed")
                return

            sync_branch = cfg.get("sync_branch", "")
            self.monitor = monitor.Monitor(cfg["local_path"], self.upl, sync_branch)
            self.monitor.start()
        except Exception as exc:
            traceback.print_exc()
            try:
                self.stop_sync()
            except Exception:
                traceback.print_exc()
            self.update_status(f"Could not start sync: {exc}")
            return

        self.connected = True
        self.connecting = False
        self.update_status()
        print(f"Connected to {cfg['server_host']}, monitoring {cfg['local_path']}")

    def stop_sync(self):
        if self.monitor:
            print("Stopping sync service...")
            try:
                self.monitor.stop()
            except RuntimeError:
                # A watcher that failed to start has no running thread to join.
                traceback.print_exc()
            finally:
                self.monitor = None
        if self.upl:
            self.upl.close()
            self.upl = None
            
        self.connected = False
        self.connecting = False
        self.update_status("Stopped")

    def shutdown(self):
        self.running = False
        self.stop_sync()
        print("Application shutdown.")

    def main(self):
        import gui_settings

        try:
            selected_index = gui_settings.choose_profile(self.config_data)
            if selected_index is None:
                return

            self.config_data["active_index"] = selected_index
            config.save_config(self.config_data)
            # A leftover command from a previous session must not connect on startup.
            if os.path.exists("control.json"):
                os.remove("control.json")

            # Commands are accepted only after a profile has been chosen.
            threading.Thread(target=self.command_loop, daemon=True).start()
            gui_settings.open_settings()
        finally:
            self.shutdown()

if __name__ == "__main__":
    import msvcrt
    import tkinter as tk
    
    LOCK_FILE = "winlinuxsync.lock"
    
    # Try to acquire exclusive lock
    try:
        lock_handle = open(LOCK_FILE, "w")
        msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
    except (IOError, OSError):
        # Another instance is running
        import tkinter.messagebox
        root = tk.Tk()
        root.withdraw()
        tkinter.messagebox.showwarning("WinLinuxSync", "Another instance is already running.")
        sys.exit(1)
    
    app = App()
    try:
        app.main()
    except KeyboardInterrupt:
        app.shutdown()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
