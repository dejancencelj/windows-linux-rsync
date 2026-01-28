import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import config

class SettingsDialog:
    def __init__(self, root, on_save_callback):
        self.root = root
        self.root.title("Settings - WinLinuxSync")
        self.root.geometry("500x450")
        self.on_save_callback = on_save_callback
        
        # Style
        style = ttk.Style()
        style.configure("Bold.TLabel", font=('Helvetica', 9, 'bold'))
        
        self.config_data = config.load_config()
        self.profiles = self.config_data.get("profiles", [])
        self.active_index = self.config_data.get("active_index", 0)

        # Profile Selection Frame
        profile_frame = tk.Frame(root)
        profile_frame.grid(row=0, column=0, columnspan=3, sticky='ew', padx=10, pady=10)
        
        tk.Label(profile_frame, text="Active Profile:").pack(side='left')
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, state="readonly")
        self.profile_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        
        tk.Button(profile_frame, text="+ New", command=self.add_profile).pack(side='left', padx=2)
        tk.Button(profile_frame, text="- Del", command=self.delete_profile).pack(side='left', padx=2)

        # Profile Details Frame
        details_frame = tk.LabelFrame(root, text="Profile Settings")
        details_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=5)

        tk.Label(details_frame, text="Profile Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.name_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Local Path:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.local_path_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.local_path_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(details_frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(details_frame, text="Remote Path:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.remote_path_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.remote_path_var, width=40).grid(row=2, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Server Host:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.host_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.host_var, width=40).grid(row=3, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Server Port:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.port_var = tk.IntVar()
        tk.Entry(details_frame, textvariable=self.port_var, width=10).grid(row=4, column=1, sticky='w', padx=5, pady=5)

        tk.Label(details_frame, text="Username:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        self.user_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.user_var, width=40).grid(row=5, column=1, padx=5, pady=5)

        tk.Label(details_frame, text="Blacklist (comma sep):").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        self.blacklist_var = tk.StringVar()
        tk.Entry(details_frame, textvariable=self.blacklist_var, width=40).grid(row=6, column=1, padx=5, pady=5)

        tk.Button(root, text="Save & Restart", command=self.save, bg="#DDDDDD", height=2).grid(row=2, column=1, pady=10)
        
        # Footer
        footer_frame = tk.Frame(root)
        footer_frame.grid(row=3, column=0, columnspan=3, pady=20)
        tk.Label(footer_frame, text="WinLinuxSync v1.0.0", fg="gray").pack()
        tk.Label(footer_frame, text="Author: DekoHack", fg="gray").pack()
        
        # Initialize
        self.current_display_index = -1
        self.refresh_profile_list()
        
        # Select active profile
        if 0 <= self.active_index < len(self.profiles):
            self.profile_combo.current(self.active_index)
            self.on_profile_change(None)

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
        self.local_path_var.set(p.get("local_path", ""))
        self.remote_path_var.set(p.get("remote_path", ""))
        self.host_var.set(p.get("server_host", ""))
        self.port_var.set(p.get("server_port", 22))
        self.user_var.set(p.get("username", ""))
        
        bl_list = p.get("blacklist", [])
        self.blacklist_var.set(", ".join(bl_list))

    def update_profile_from_ui(self, idx):
        if 0 <= idx < len(self.profiles):
            self.profiles[idx] = {
                "name": self.name_var.get(),
                "local_path": self.local_path_var.get(),
                "remote_path": self.remote_path_var.get(),
                "server_host": self.host_var.get(),
                "server_port": self.port_var.get(),
                "server_port": self.port_var.get(),
                "username": self.user_var.get(),
                "blacklist": [x.strip() for x in self.blacklist_var.get().split(',') if x.strip()]
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

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.local_path_var.set(folder)

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
