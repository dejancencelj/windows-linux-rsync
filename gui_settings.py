import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import os
import config

class SettingsDialog:
    def __init__(self, root, on_save_callback):
        self.root = root
        self.root.title("Settings - WinLinuxSync")
        self.root.geometry("600x650") # Increased size
        self.on_save_callback = on_save_callback
        
        # Style
        style = ttk.Style()
        style.configure("Bold.TLabel", font=('Helvetica', 9, 'bold'))
        
        self.config_data = config.load_config()
        self.profiles = self.config_data.get("profiles", [])
        self.active_index = self.config_data.get("active_index", 0)

        # Profile Selection Frame
        profile_frame = tk.Frame(root)
        profile_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=5)
        
        # Status Dashboard
        status_frame = tk.LabelFrame(root, text="System Status")
        status_frame.grid(row=0, column=0, columnspan=3, sticky='ew', padx=10, pady=5)
        
        self.ssh_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.ssh_canvas.pack(side='left', padx=5)
        self.ssh_circle = self.ssh_canvas.create_oval(2, 2, 18, 18, fill="red")
        tk.Label(status_frame, text="SSH Connection").pack(side='left')
        
        tk.Label(status_frame, text="   |   ").pack(side='left')

        self.mon_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.mon_canvas.pack(side='left', padx=5)
        self.mon_circle = self.mon_canvas.create_oval(2, 2, 18, 18, fill="red")
        tk.Label(status_frame, text="Folder Monitor").pack(side='left')
        
        tk.Label(status_frame, text="   |   ").pack(side='left')

        self.git_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.git_canvas.pack(side='left', padx=5)
        self.git_circle = self.git_canvas.create_oval(2, 2, 18, 18, fill="red")
        tk.Label(status_frame, text="Git Repo").pack(side='left')

        tk.Label(status_frame, text="   |   ").pack(side='left')
        tk.Button(status_frame, text="Connect", command=self.manual_connect, bg="#DDFFDD").pack(side='left', padx=5)
        tk.Button(status_frame, text="Disconnect", command=self.manual_disconnect, bg="#FFCCCC").pack(side='left', padx=5)
        
        tk.Label(profile_frame, text="Active Profile:").pack(side='left')
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, state="readonly")
        self.profile_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        
        tk.Button(profile_frame, text="Switch", command=self.switch_profile, bg="#AADDFF").pack(side='left', padx=2)
        tk.Button(profile_frame, text="+ New", command=self.add_profile).pack(side='left', padx=2)
        tk.Button(profile_frame, text="- Del", command=self.delete_profile).pack(side='left', padx=2)

        # Git-only info banner
        info_frame = tk.Frame(root, bg="#FFF8DC", relief='groove', bd=1)
        info_frame.grid(row=2, column=0, columnspan=3, sticky='ew', padx=10, pady=(0, 2))
        tk.Label(
            info_frame,
            text="⚠  This app only syncs files that have changes visible in Git. The local folder must be a Git repository.",
            bg="#FFF8DC", fg="#7A5C00", font=('Helvetica', 9), wraplength=560, justify='left', pady=4
        ).pack(fill='x', padx=8)

        # Profile Details Frame
        details_frame = tk.LabelFrame(root, text="Profile Settings")
        details_frame.grid(row=3, column=0, columnspan=3, sticky='ew', padx=10, pady=5)

        tk.Label(details_frame, text="Profile Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.name_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Local Path (Git repo):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.local_path_var = tk.StringVar()
        self.local_path_var.trace_add("write", self._on_local_path_change)
        tk.Entry(details_frame, textvariable=self.local_path_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(details_frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, padx=5, pady=5)
        self.git_warning_label = tk.Label(details_frame, text="", fg="#CC4400", font=('Helvetica', 8))
        self.git_warning_label.grid(row=1, column=3, sticky='w', padx=5)

        tk.Label(details_frame, text="Sync Branch (optional):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.sync_branch_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.sync_branch_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        tk.Label(details_frame, text="Leave empty to sync all branches", fg="gray", font=('Helvetica', 8)).grid(row=2, column=2, columnspan=2, sticky='w', padx=5)

        tk.Label(details_frame, text="Remote Path:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.remote_path_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.remote_path_var, width=40).grid(row=3, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Server Host:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.host_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.host_var, width=40).grid(row=4, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Server Port:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        self.port_var = tk.IntVar()
        tk.Entry(details_frame, textvariable=self.port_var, width=10).grid(row=5, column=1, sticky='w', padx=5, pady=5)

        tk.Label(details_frame, text="Username:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        self.user_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.user_var, width=40).grid(row=6, column=1, padx=5, pady=5)


        # Log Frame
        log_frame = tk.LabelFrame(root, text="Activity Log")
        log_frame.grid(row=4, column=0, columnspan=3, sticky='nsew', padx=10, pady=5)
        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        tk.Button(root, text="Save & Close", command=self.save, bg="#DDDDDD", height=1).grid(row=5, column=1, pady=5)

        # Footer
        footer_frame = tk.Frame(root)
        footer_frame.grid(row=6, column=0, columnspan=3, pady=20)
        tk.Label(footer_frame, text="WinLinuxSync v2026.02.18", fg="gray").pack()
        tk.Label(footer_frame, text="Author: DekoHack (github.com/dejancencelj)  |  Built with Claude Code (Anthropic)", fg="gray").pack()
        
        # Initialize
        self.current_display_index = -1
        self.refresh_profile_list()
        
        # Select active profile
        if 0 <= self.active_index < len(self.profiles):
            self.profile_combo.current(self.active_index)
            self.on_profile_change(None)

        # Start polling status and logs separately
        self.poll_status()
        self.update_logs()

    def manual_connect(self):
        import json
        try:
            with open("control.json", "w") as f:
                json.dump({"command": "reconnect"}, f)
        except Exception:
            pass

    def manual_disconnect(self):
        import json
        try:
            with open("control.json", "w") as f:
                json.dump({"command": "stop"}, f)
        except Exception:
            pass

    def switch_profile(self):
        """Save current profile to config and trigger reconnect with new profile."""
        import json
        # Save current profile fields first
        if self.current_display_index != -1:
            self.update_profile_from_ui(self.current_display_index)
        
        # Set active index to selected profile
        active_idx = self.profile_combo.current()
        if active_idx == -1:
            return
        
        # Save to config file
        new_config = {
            "profiles": self.profiles,
            "active_index": active_idx
        }
        config.save_config(new_config)
        
        # Trigger reconnect
        try:
            with open("control.json", "w") as f:
                json.dump({"command": "reconnect"}, f)
        except Exception:
            pass
        
        from tkinter import messagebox
        messagebox.showinfo("Profile Switched", f"Switched to: {self.profiles[active_idx].get('name')}")


    def poll_status(self):
        import json
        import os
        try:
            if os.path.exists("status.json"):
                with open("status.json", "r") as f:
                    status = json.load(f)
                    
                # Update UI
                ssh_color = "green" if status.get("connected") else "red"
                mon_color = "green" if status.get("monitoring") else "red"
                
                self.ssh_canvas.itemconfig(self.ssh_circle, fill=ssh_color)
                self.mon_canvas.itemconfig(self.mon_circle, fill=mon_color)
                    
        except Exception:
            pass
            
        self.root.after(2000, self.poll_status)  # Slower polling for responsiveness

    def update_logs(self):
        import os
        try:
            if os.path.exists("sync.log"):
                with open("sync.log", "r", encoding="utf-8", errors="ignore") as f:
                    # Only read last 10KB to prevent freezing on large logs
                    f.seek(0, 2)  # Seek to end
                    size = f.tell()
                    max_bytes = 10000
                    if size > max_bytes:
                        f.seek(size - max_bytes)
                        f.readline()  # Skip partial line
                    else:
                        f.seek(0)
                    content = f.read()
                    
                    self.log_text.config(state='normal')
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(tk.END, content)
                    self.log_text.see(tk.END)
                    self.log_text.config(state='disabled')
        except Exception:
            pass
        self.root.after(2000, self.update_logs)  # Slower polling to reduce CPU
        

    def refresh_profile_list(self):
        names = [p.get("name", "Unnamed") for p in self.profiles]
        self.profile_combo['values'] = names
        if 0 <= self.current_display_index < len(names):
             self.profile_combo.current(self.current_display_index)

    def on_profile_change(self, event):
        idx = self.profile_combo.current()
        if idx == -1: return
        
        # Save current fields to the PREVIOUS profile in memory before switching?
        # Yes, otherwise changes to one profile are lost when switching to another in the dropdown 
        # unless we require explicit "Save" for each.
        # Let's auto-save to memory on switch.
        if self.current_display_index != -1 and self.current_display_index < len(self.profiles):
            self.update_profile_from_ui(self.current_display_index)

        self.current_display_index = idx
        p = self.profiles[idx]
        
        self.name_var.set(p.get("name", ""))
        self.local_path_var.set(p.get("local_path", ""))  # triggers _on_local_path_change via trace
        self.sync_branch_var.set(p.get("sync_branch", ""))
        self.remote_path_var.set(p.get("remote_path", ""))
        self.host_var.set(p.get("server_host", ""))
        self.port_var.set(p.get("server_port", 22))
        self.user_var.set(p.get("username", ""))

    def update_profile_from_ui(self, idx):
        if 0 <= idx < len(self.profiles):
            self.profiles[idx] = {
                "name": self.name_var.get(),
                "local_path": self.local_path_var.get(),
                "sync_branch": self.sync_branch_var.get(),
                "remote_path": self.remote_path_var.get(),
                "server_host": self.host_var.get(),
                "server_port": self.port_var.get(),
                "username": self.user_var.get()
            }

    def add_profile(self):
        # Save current first
        if self.current_display_index != -1:
             self.update_profile_from_ui(self.current_display_index)
             
        new_p = config.DEFAULT_PROFILE.copy()
        new_p["name"] = f"Profile {len(self.profiles) + 1}"
        self.profiles.append(new_p)
        self.refresh_profile_list()
        self.profile_combo.current(len(self.profiles) - 1)
        self.on_profile_change(None)

    def delete_profile(self):
        if len(self.profiles) <= 1:
            messagebox.showerror("Error", "Cannot delete the only profile.")
            return
            
        idx = self.profile_combo.current()
        if idx == -1: return
        
        if messagebox.askyesno("Confirm", "Delete this profile?"):
            del self.profiles[idx]
            self.current_display_index = -1 # Was deleted
            
            # If we deleted the active index or one before it, active index shifts? 
            # We just reset to 0 for simplicity.
            self.active_index = 0
            
            self.refresh_profile_list()
            self.profile_combo.current(0)
            self.on_profile_change(None)

    def _on_local_path_change(self, *args):
        """Update the git indicator and inline warning whenever the local path changes."""
        path = self.local_path_var.get()
        is_git = os.path.isdir(os.path.join(path, '.git')) if path else False
        color = "green" if is_git else "red"
        self.git_canvas.itemconfig(self.git_circle, fill=color)
        if path and not is_git:
            self.git_warning_label.config(text="⚠ Not a Git repo — uploads will be suppressed")
        else:
            self.git_warning_label.config(text="")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.local_path_var.set(folder)
            if not os.path.isdir(os.path.join(folder, '.git')):
                messagebox.showwarning(
                    "Not a Git Repository",
                    f"The selected folder does not contain a .git directory:\n\n{folder}\n\n"
                    "WinLinuxSync only uploads files with changes visible in Git.\n"
                    "No files will be synced until a Git repository is selected."
                )

    def save(self):
        # Update current displayed profile to memory
        if self.current_display_index != -1:
            self.update_profile_from_ui(self.current_display_index)

        # The currently selected combobox item becomes the ACTIVE profile
        active_idx = self.profile_combo.current()
        if active_idx == -1: active_idx = 0

        new_config = {
            "profiles": self.profiles,
            "active_index": active_idx
        }
        
        config.save_config(new_config)
        messagebox.showinfo("Saved", f"Configuration saved.\nActive Profile: {self.profiles[active_idx].get('name')}")
        
        if self.on_save_callback:
            self.on_save_callback(new_config)
        self.root.destroy()

def open_settings(on_save_callback=None):
    root = tk.Tk()
    app = SettingsDialog(root, on_save_callback)
    root.mainloop()

if __name__ == "__main__":
    open_settings()
