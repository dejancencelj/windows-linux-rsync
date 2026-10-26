import copy
import json
import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, ttk

import config

BG = "#f1f4f5"
SURFACE = "#ffffff"
TEXT = "#233638"
MUTED = "#687b7e"
ACCENT = "#216858"
ERROR = "#b14637"


def apply_theme(root):
    root.configure(bg=BG)
    tkfont.nametofont("TkDefaultFont", root=root).configure(family="Segoe UI", size=10)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", font=("Segoe UI", 10), foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Surface.TLabel", background=SURFACE)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("SurfaceMuted.TLabel", background=SURFACE, foreground=MUTED, font=("Segoe UI", 9))
    style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"))
    style.configure("Section.TLabel", background=SURFACE, font=("Segoe UI", 12, "bold"))
    style.configure("Status.TLabel", background=SURFACE, font=("Segoe UI", 12, "bold"))
    style.configure("TButton", background="#e6ecec", foreground=TEXT, borderwidth=0,
                    padding=(12, 7), focusthickness=2, focuscolor="#9fbdb3")
    style.map("TButton", background=[("pressed", "#cbd9d5"), ("active", "#d9e3e1")],
              foreground=[("disabled", "#91a09f")])
    style.configure("Accent.TButton", background=ACCENT, foreground=SURFACE)
    style.map("Accent.TButton", background=[("disabled", "#dbe5e1"), ("pressed", "#174d40"),
                                             ("active", "#2b7a68")],
              foreground=[("disabled", "#8a9d95")])
    style.configure("TEntry", fieldbackground="#f8fafa", bordercolor="#dbe3e3", padding=(8, 5))
    style.map("TEntry", bordercolor=[("focus", ACCENT)])
    style.configure("TCombobox", fieldbackground=SURFACE, background="#e6ecec",
                    bordercolor="#dbe3e3", padding=(8, 6), arrowsize=14)
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE)],
              foreground=[("readonly", TEXT)], bordercolor=[("focus", ACCENT)])
    style.configure("TSeparator", background="#e6ecec")


def place_window(root, width, height):
    width = min(width, root.winfo_screenwidth() - 60)
    height = min(height, root.winfo_screenheight() - 100)
    x = max(0, (root.winfo_screenwidth() - width) // 2)
    y = max(0, (root.winfo_screenheight() - height) // 2 - 25)
    root.geometry(f"{width}x{height}+{x}+{y}")


class ProfileChooser:
    def __init__(self, root, profiles):
        self.root = root
        self.profiles = profiles
        self.selected_index = None
        root.title("Choose Profile - WinLinuxSync")
        apply_theme(root)
        place_window(root, 530, 300)
        root.resizable(False, False)
        frame = ttk.Frame(root, padding=26)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text="Choose your workspace", style="Title.TLabel").pack(anchor='w')
        ttk.Label(frame, text="Open a profile, then click Connect when you are ready.",
                  style="Muted.TLabel").pack(anchor='w', pady=(4, 20))
        self.profile_combo = ttk.Combobox(
            frame, state="readonly", width=50,
            values=[profile.get("name", "Unnamed") for profile in profiles]
        )
        self.profile_combo.pack(fill='x')
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        self.folder_label = ttk.Label(frame, text="", wraplength=460, style="Muted.TLabel")
        self.folder_label.pack(anchor='w', pady=12)
        buttons = ttk.Frame(frame)
        buttons.pack(side='bottom', fill='x')
        self.start_button = ttk.Button(buttons, text="Open workspace", style="Accent.TButton",
                                       command=self.confirm, state='disabled')
        self.start_button.pack(side='right')
        ttk.Button(buttons, text="Cancel", command=root.destroy).pack(side='right', padx=(0, 8))
        root.bind('<Return>', lambda event: self.confirm())
        root.bind('<Escape>', lambda event: root.destroy())
        self.profile_combo.focus_set()

    def on_profile_change(self, event=None):
        index = self.profile_combo.current()
        if index != -1:
            self.folder_label.config(text=self.profiles[index].get("local_path", ""))
            self.start_button.config(state='normal')

    def confirm(self):
        index = self.profile_combo.current()
        if index == -1:
            return
        self.selected_index = index
        self.root.destroy()


def choose_profile(config_data):
    root = tk.Tk()
    chooser = ProfileChooser(root, config_data.get("profiles", []))
    root.mainloop()
    return chooser.selected_index


class SettingsDialog:
    def __init__(self, root):
        self.root = root
        root.title("WinLinuxSync - Workspace")
        apply_theme(root)
        place_window(root, 1060, 720)
        root.minsize(900, 640)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.config_data = copy.deepcopy(config.load_config())
        self.profiles = self.config_data.get("profiles") or [config.DEFAULT_PROFILE.copy()]
        self.active_index = self.config_data.get("active_index", 0)
        self.current_display_index = -1
        self._after_ids = {}
        self._last_log = None
        self._connected = False
        self._connecting = False
        self._local_error = None

        shell = ttk.Frame(root, padding=(24, 16, 24, 12))
        shell.pack(fill='both', expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(3, weight=1)
        self._build_header(shell)
        self._build_profile_bar(shell)
        self._build_connection_bar(shell)
        body = ttk.Frame(shell)
        body.grid(row=3, column=0, sticky='nsew', pady=(14, 0))
        body.columnconfigure(0, weight=6, uniform='body')
        body.columnconfigure(1, weight=5, uniform='body')
        body.rowconfigure(0, weight=1)
        self._build_form(body)
        self._build_log(body)
        footer = ttk.Frame(shell)
        footer.grid(row=4, column=0, sticky='ew', pady=(12, 0))
        self.feedback_label = ttk.Label(footer, text="Profiles stay on this device.", style="Muted.TLabel")
        self.feedback_label.pack(side='left')
        ttk.Button(footer, text="Close", command=self.close).pack(side='right')
        ttk.Button(footer, text="Save profile", command=self.save).pack(side='right', padx=(0, 8))
        root.bind('<Control-s>', lambda event: self.save())
        self.refresh_profile_list()
        index = self.active_index if 0 <= self.active_index < len(self.profiles) else 0
        self.profile_combo.current(index)
        self.on_profile_change()
        self.poll_status()
        self.update_logs()

    def _build_header(self, parent):
        header = ttk.Frame(parent)
        header.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        mark = tk.Canvas(header, width=42, height=42, bg=ACCENT, highlightthickness=0)
        mark.pack(side='left', padx=(0, 12))
        mark.create_line(10, 15, 31, 15, arrow='last', fill=SURFACE, width=2)
        mark.create_line(31, 27, 10, 27, arrow='last', fill=SURFACE, width=2)
        title = ttk.Frame(header)
        title.pack(side='left')
        ttk.Label(title, text="WinLinuxSync", style="Title.TLabel").pack(anchor='w')
        ttk.Label(title, text="Your local changes, on your remote workspace.", style="Muted.TLabel").pack(anchor='w')
        ttk.Label(header, text="Windows  →  Linux\nSFTP / Git-aware sync", justify='right',
                  style="Muted.TLabel").pack(side='right')

    def _build_profile_bar(self, parent):
        bar = ttk.Frame(parent, style="Surface.TFrame", padding=(16, 12))
        bar.grid(row=1, column=0, sticky='ew')
        ttk.Label(bar, text="Workspace", style="Surface.TLabel").pack(side='left', padx=(0, 14))
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(bar, textvariable=self.profile_var, state="readonly", width=34)
        self.profile_combo.pack(side='left', fill='x', expand=True)
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        ttk.Button(bar, text="New profile", command=self.add_profile).pack(side='left', padx=(16, 8))
        ttk.Button(bar, text="Delete", command=self.delete_profile).pack(side='left')

    def _build_connection_bar(self, parent):
        bar = ttk.Frame(parent, style="Surface.TFrame", padding=(16, 14))
        bar.grid(row=2, column=0, sticky='ew', pady=(2, 0))
        bar.columnconfigure(0, weight=1)
        summary = ttk.Frame(bar, style="Surface.TFrame")
        summary.grid(row=0, column=0, sticky='w')
        self.connection_label = ttk.Label(summary, text="Disconnected", style="Status.TLabel")
        self.connection_label.pack(anchor='w')
        self.connection_hint = ttk.Label(summary, text="Click Connect to start syncing.", style="SurfaceMuted.TLabel")
        self.connection_hint.pack(anchor='w', pady=(3, 0))
        indicators = ttk.Frame(bar, style="Surface.TFrame")
        indicators.grid(row=0, column=1, padx=20)
        self.ssh_label = ttk.Label(indicators, text="SSH offline", style="SurfaceMuted.TLabel")
        self.ssh_label.pack(anchor='w')
        self.mon_label = ttk.Label(indicators, text="Watcher stopped", style="SurfaceMuted.TLabel")
        self.mon_label.pack(anchor='w', pady=(3, 0))
        buttons = ttk.Frame(bar, style="Surface.TFrame")
        buttons.grid(row=0, column=2)
        self.disconnect_button = ttk.Button(buttons, text="Disconnect", command=self.manual_disconnect, state='disabled')
        self.disconnect_button.pack(side='left', padx=(0, 8))
        self.connect_button = ttk.Button(buttons, text="Connect", style="Accent.TButton", command=self.manual_connect)
        self.connect_button.pack(side='left')
        self.status_error_label = ttk.Label(bar, text="", foreground=ERROR, style="Surface.TLabel", wraplength=780)
        self.status_error_label.grid(row=1, column=0, columnspan=3, sticky='w', pady=(8, 0))
        self.status_error_label.grid_remove()

    def _build_form(self, parent):
        panel = ttk.Frame(parent, style="Surface.TFrame", padding=18)
        panel.grid(row=0, column=0, sticky='nsew', padx=(0, 7))
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        self.form_canvas = tk.Canvas(panel, bg=SURFACE, highlightthickness=0, width=1, height=1)
        self.form_canvas.grid(row=0, column=0, sticky='nsew')
        self.form_scrollbar = ttk.Scrollbar(panel, orient='vertical', command=self.form_canvas.yview)
        self.form_canvas.config(yscrollcommand=self.form_scrollbar.set)
        form = ttk.Frame(self.form_canvas, style="Surface.TFrame")
        form_window = self.form_canvas.create_window((0, 0), window=form, anchor='nw')
        def resize_form(event=None):
            self.form_canvas.itemconfigure(form_window, width=self.form_canvas.winfo_width())
            self.form_canvas.configure(scrollregion=self.form_canvas.bbox('all'))
            if form.winfo_reqheight() > self.form_canvas.winfo_height():
                self.form_scrollbar.grid(row=0, column=1, sticky='ns', padx=(6, 0))
            else:
                self.form_scrollbar.grid_remove()
        self.form_canvas.bind('<Configure>', resize_form)
        form.bind('<Configure>', resize_form)
        def scroll_form(event):
            if str(event.widget).startswith(str(form)) or event.widget == self.form_canvas:
                if form.winfo_reqheight() > self.form_canvas.winfo_height():
                    self.form_canvas.yview_scroll(-int(event.delta / 120), 'units')
                    return 'break'
        self.root.bind('<MouseWheel>', scroll_form, add='+')
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Profile settings", style="Section.TLabel").grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Label(form, text="Save your settings. Connect when you are ready.",
                  style="SurfaceMuted.TLabel").grid(row=1, column=0, columnspan=3, sticky='w', pady=(3, 12))
        self.name_var = tk.StringVar()
        self.local_path_var = tk.StringVar()
        self.sync_branch_var = tk.StringVar()
        self.remote_path_var = tk.StringVar()
        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar(value="22")
        self.user_var = tk.StringVar()
        fields = [(2, "Profile name", self.name_var), (3, "Local folder", self.local_path_var),
                  (5, "Sync branch", self.sync_branch_var), (8, "Remote folder", self.remote_path_var),
                  (9, "Server host", self.host_var), (10, "Username", self.user_var), (11, "SSH port", self.port_var)]
        self.entries = {}
        for row, label, variable in fields:
            ttk.Label(form, text=label, style="Surface.TLabel").grid(row=row, column=0, sticky='w', padx=(0, 12), pady=4)
            entry = ttk.Entry(form, textvariable=variable, width=8 if row == 11 else 24)
            entry.grid(row=row, column=1, columnspan=1 if row in (3, 11) else 2,
                       sticky='w' if row == 11 else 'ew', pady=4)
            self.entries[label] = entry
        ttk.Button(form, text="Browse", command=self.browse_folder).grid(row=3, column=2, padx=(8, 0))
        self.git_warning_label = ttk.Label(form, text="", style="SurfaceMuted.TLabel", wraplength=330)
        self.git_warning_label.grid(row=4, column=1, columnspan=2, sticky='w', pady=(0, 3))
        ttk.Label(form, text="Optional · blank means all branches", style="SurfaceMuted.TLabel").grid(
            row=6, column=1, columnspan=2, sticky='w', pady=(0, 6))
        ttk.Separator(form).grid(row=7, column=0, columnspan=3, sticky='ew', pady=(4, 8))
        self.local_path_var.trace_add("write", self._on_local_path_change)

    def _build_log(self, parent):
        panel = ttk.Frame(parent, style="Surface.TFrame", padding=18)
        panel.grid(row=0, column=1, sticky='nsew', padx=(7, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)
        ttk.Label(panel, text="Activity", style="Section.TLabel").grid(row=0, column=0, sticky='w')
        ttk.Label(panel, text="Recent connection and file transfer events", style="SurfaceMuted.TLabel").grid(
            row=1, column=0, sticky='w', pady=(3, 14))
        log_frame = ttk.Frame(panel)
        log_frame.grid(row=2, column=0, sticky='nsew')
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=9, width=30, state='disabled', wrap='word',
                                font=('Consolas', 10), bg="#1b2b2e", fg="#dce6e5", relief='flat',
                                padx=14, pady=14, insertbackground=SURFACE, selectbackground="#3f625c",
                                spacing1=2, spacing3=3, highlightthickness=0)
        self.log_text.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.log_text.config(yscrollcommand=scrollbar.set)
        self.log_text.tag_configure('error', foreground="#f5a498")
        self.log_text.tag_configure('success', foreground="#8fd0b3")
        ttk.Label(panel, text="Only files with visible Git changes are uploaded.",
                  style="SurfaceMuted.TLabel", wraplength=360).grid(row=3, column=0, sticky='w', pady=(12, 0))

    def _send_command(self, command):
        try:
            with open("control.json", "w") as handle:
                json.dump({"command": command}, handle)
            return True
        except OSError as exc:
            self._show_error(f"Could not send command: {exc}")
            return False

    def manual_connect(self):
        if not self._save_profile():
            return
        profile = self.profiles[self.current_display_index]
        if not profile.get("server_host") or not profile.get("local_path"):
            self._show_error("Enter a server host and a local folder before connecting.")
            return
        if self._send_command("reconnect"):
            self.render_status({"connecting": True})
            self.feedback_label.config(text="Connecting to the selected workspace…")

    def manual_disconnect(self):
        if self._send_command("stop"):
            self.connection_hint.config(text="Stopping the connection and folder watcher…")

    def _show_error(self, message, local=True):
        if local:
            self._local_error = message
        self.status_error_label.config(text=message)
        self.status_error_label.grid()

    def render_status(self, status):
        self._connected = bool(status.get("connected"))
        self._connecting = bool(status.get("connecting"))
        monitoring = bool(status.get("monitoring"))
        title = "Connecting…" if self._connecting else "Connected" if self._connected else "Disconnected"
        self.connection_label.config(text=title, foreground=ACCENT if self._connected else TEXT)
        hint = "Watching your local folder for Git changes." if monitoring else "Click Connect to start syncing."
        self.connection_hint.config(text="Opening the SSH connection…" if self._connecting else hint)
        self.ssh_label.config(text="SSH connected" if self._connected else "SSH offline",
                              foreground=ACCENT if self._connected else MUTED)
        self.mon_label.config(text="Watcher running" if monitoring else "Watcher stopped",
                              foreground=ACCENT if monitoring else MUTED)
        self.connect_button.config(text="Connecting…" if self._connecting else "Connected" if self._connected else "Connect",
                                   state='disabled' if self._connecting or self._connected else 'normal')
        self.disconnect_button.config(state='normal' if self._connected or self._connecting else 'disabled')
        error = self._local_error or status.get("error")
        if error and error != "Stopped":
            self._show_error(error, local=False)
        else:
            self.status_error_label.grid_remove()

    def _schedule(self, name, delay, callback):
        self._after_ids[name] = self.root.after(delay, callback)

    def poll_status(self):
        try:
            with open("status.json", "r") as handle:
                status = json.load(handle)
            if not os.path.exists("control.json"):
                self.render_status(status)
        except (OSError, ValueError):
            pass
        self._schedule('status', 500, self.poll_status)

    def update_logs(self):
        content = ""
        try:
            with open("sync.log", "rb") as handle:
                size = handle.seek(0, 2)
                handle.seek(max(0, size - 12000))
                if size > 12000:
                    handle.readline()
                content = handle.read().decode('utf-8', errors='replace')
        except OSError:
            pass
        if content != self._last_log:
            at_bottom = self.log_text.yview()[1] >= 0.98
            position = self.log_text.yview()[0]
            self.log_text.config(state='normal')
            self.log_text.delete('1.0', 'end')
            for line in (content or "No activity yet.\nClick Connect to start syncing.").splitlines(keepends=True):
                lower = line.lower()
                tag = 'error' if any(word in lower for word in ('failed', 'error', 'traceback')) else (
                    'success' if 'successful' in lower or lower.startswith('connected to') else '')
                self.log_text.insert('end', line, (tag,) if tag else ())
            self.log_text.config(state='disabled')
            if at_bottom or self._last_log is None:
                self.log_text.see('end')
            else:
                self.log_text.yview_moveto(position)
            self._last_log = content
        self._schedule('logs', 1500, self.update_logs)

    def refresh_profile_list(self):
        self.profile_combo['values'] = [profile.get("name", "Unnamed") for profile in self.profiles]
        if 0 <= self.current_display_index < len(self.profiles):
            self.profile_combo.current(self.current_display_index)

    def on_profile_change(self, event=None):
        index = self.profile_combo.current()
        if index == -1:
            return
        previous = self.current_display_index
        if previous != -1 and previous != index:
            if not self.update_profile_from_ui(previous):
                self.profile_combo.current(previous)
                return
            self.manual_disconnect()
        self.current_display_index = index
        self.active_index = index
        profile = self.profiles[index]
        self.name_var.set(profile.get("name", ""))
        self.local_path_var.set(profile.get("local_path", ""))
        self.sync_branch_var.set(profile.get("sync_branch", ""))
        self.remote_path_var.set(profile.get("remote_path", ""))
        self.host_var.set(profile.get("server_host", ""))
        self.port_var.set(str(profile.get("server_port", 22)))
        self.user_var.set(profile.get("username", ""))
        if previous != -1 and previous != index:
            self._save_profile()
            self.feedback_label.config(text="Profile selected. Click Connect to start syncing.")

    def update_profile_from_ui(self, index):
        try:
            port = int(self.port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            self._show_error("SSH port must be a number between 1 and 65535.")
            return False
        self.profiles[index].update({
            "name": self.name_var.get().strip() or "Unnamed profile",
            "local_path": self.local_path_var.get().strip(),
            "sync_branch": self.sync_branch_var.get().strip(),
            "remote_path": self.remote_path_var.get().strip(),
            "server_host": self.host_var.get().strip(),
            "server_port": port,
            "username": self.user_var.get().strip(),
        })
        return True

    def _save_profile(self):
        index = self.profile_combo.current()
        if index == -1 or not self.update_profile_from_ui(index):
            return False
        self.config_data.update(profiles=self.profiles, active_index=index)
        try:
            config.save_config(self.config_data)
        except OSError as exc:
            self._show_error(f"Could not save profile: {exc}")
            return False
        self.refresh_profile_list()
        self._local_error = None
        self.status_error_label.grid_remove()
        return True

    def save(self):
        if self._save_profile():
            if self._connected or self._connecting:
                self.manual_disconnect()
            self.feedback_label.config(text="Profile saved. Click Connect when you are ready.")

    def add_profile(self):
        if not self.update_profile_from_ui(self.current_display_index):
            return
        profile = config.DEFAULT_PROFILE.copy()
        profile['name'] = f"Profile {len(self.profiles) + 1}"
        self.profiles.append(profile)
        self.refresh_profile_list()
        self.profile_combo.current(len(self.profiles) - 1)
        self.on_profile_change()
        self.entries['Profile name'].focus_set()
        self.entries['Profile name'].selection_range(0, 'end')

    def delete_profile(self):
        if len(self.profiles) <= 1:
            self._show_error("Keep at least one profile. You can edit its settings instead.")
            return
        index = self.profile_combo.current()
        if not messagebox.askyesno("Delete profile", f"Delete {self.profiles[index].get('name')}?", parent=self.root):
            return
        self.manual_disconnect()
        del self.profiles[index]
        self.current_display_index = -1
        self.refresh_profile_list()
        self.profile_combo.current(min(index, len(self.profiles) - 1))
        self.on_profile_change()
        self._save_profile()
        self.feedback_label.config(text="Profile deleted. Choose a workspace to connect.")

    def _on_local_path_change(self, *args):
        path = self.local_path_var.get()
        exists = bool(path) and os.path.isdir(path)
        is_git = exists and os.path.isdir(os.path.join(path, '.git'))
        text = "Git repository detected" if is_git else "Folder does not exist" if path and not exists else (
            "Not a Git repository · files will not sync" if path else "Choose a local Git repository")
        self.git_warning_label.config(text=text, foreground=ACCENT if is_git else ERROR if path else MUTED)

    def browse_folder(self):
        folder = filedialog.askdirectory(parent=self.root)
        if folder:
            self.local_path_var.set(folder)

    def close(self):
        for after_id in self._after_ids.values():
            self.root.after_cancel(after_id)
        self._after_ids.clear()
        self.root.destroy()


def open_settings():
    root = tk.Tk()
    SettingsDialog(root)
    root.mainloop()


if __name__ == "__main__":
    open_settings()
