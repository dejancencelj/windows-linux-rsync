import time
import os
import threading
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitChecker:
    def __init__(self, local_base_path, sync_branch=""):
        self.local_base_path = local_base_path
        self.sync_branch = sync_branch
        self.is_git_repo = os.path.isdir(os.path.join(local_base_path, '.git'))
        if self.is_git_repo:
            print(f"Git repo detected at {local_base_path}. Git-aware filtering enabled.")
            if self.sync_branch:
                print(f"Will only sync when branch '{self.sync_branch}' is active.")
        else:
            print(f"No .git directory found at {local_base_path}. All file uploads will be suppressed.")

    def get_current_branch(self) -> str:
        if not self.is_git_repo:
            return ""
        try:
            # Try git branch --show-current first (git >= 2.22)
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.local_base_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            # Fallback: git rev-parse --abbrev-ref HEAD
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.local_base_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                if branch != 'HEAD':  # HEAD means detached
                    return branch
        except Exception:
            pass
        return ""

    def is_file_changed(self, file_path) -> bool:
        """Returns True if git sees changes for this file (modified, added, or untracked).
        Returns False if the file is clean, gitignored, or if git is unavailable.
        """
        if not self.is_git_repo:
            return False

        if self.sync_branch:
            current_branch = self.get_current_branch()
            if current_branch != self.sync_branch:
                print(f"Branch mismatch: current '{current_branch}' != sync '{self.sync_branch}'")
                return False

        # Use relative path for git status to avoid Windows path casing issues
        try:
            rel_path = os.path.relpath(file_path, self.local_base_path)
        except ValueError:
            rel_path = file_path  # fallback for cross-drive paths

        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain', rel_path],
                cwd=self.local_base_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print(f"Warning: git status returned non-zero for {rel_path}")
                return False
            is_changed = bool(result.stdout.strip())
            if not is_changed:
                print(f"Git says file is clean (no pending changes): {rel_path}")
            return is_changed
        except FileNotFoundError:
            print("Warning: git not found on PATH. File upload suppressed.")
            return False
        except subprocess.TimeoutExpired:
            print(f"Warning: git status timed out for {file_path}.")
            return False
        except Exception as e:
            print(f"Warning: git check failed: {e}")
            return False


class SyncHandler(FileSystemEventHandler):
    def __init__(self, uploader, local_base_path, sync_branch=""):
        self.uploader = uploader
        self.local_base_path = local_base_path
        self.paused = False

        # Debouncing: track last upload time per file
        self.last_upload = {}
        self.debounce_seconds = 2  # Ignore duplicate events within 2 seconds
        self.lock = threading.Lock()

        # Git-aware filtering: check once at startup if this is a git repo
        self.git_checker = GitChecker(local_base_path, sync_branch)

    def should_upload(self, file_path):
        """Check if enough time has passed since last upload of this file."""
        with self.lock:
            now = time.time()
            last = self.last_upload.get(file_path, 0)
            if now - last < self.debounce_seconds:
                return False
            self.last_upload[file_path] = now
            return True

    def process_event(self, event):
        if self.paused or event.is_directory:
            return

        # Calculate relative path
        relative_path = os.path.relpath(event.src_path, self.local_base_path)

        # Skip temp/swap files
        basename = os.path.basename(event.src_path)
        if basename.startswith('.') or basename.endswith('.tmp') or basename.endswith('~'):
            return

        # Debounce check
        if not self.should_upload(event.src_path):
            return

        # Git-aware filter: only upload if git sees changes for this file
        if not self.git_checker.is_file_changed(event.src_path):
            return

        print(f"Detected change in: {relative_path}")
        self.uploader.upload_file(event.src_path, relative_path)

    def on_modified(self, event):
        self.process_event(event)

    def on_created(self, event):
        self.process_event(event)
        
    def on_moved(self, event):
        if not event.is_directory:
            relative_path = os.path.relpath(event.dest_path, self.local_base_path)
            
            # Skip temp files
            basename = os.path.basename(event.dest_path)
            if basename.startswith('.') or basename.endswith('.tmp') or basename.endswith('~'):
                return
            
            if not self.should_upload(event.dest_path):
                return

            # Git-aware filter: only upload if git sees changes for this file
            if not self.git_checker.is_file_changed(event.dest_path):
                return

            print(f"File moved to: {relative_path}")
            self.uploader.upload_file(event.dest_path, relative_path)

class Monitor:
    def __init__(self, local_path, uploader, sync_branch=""):
        self.local_path = local_path
        self.uploader = uploader
        self.observer = Observer()
        self.handler = SyncHandler(uploader, local_path, sync_branch)

    def set_paused(self, paused):
        self.handler.paused = paused
        print(f"Monitor paused: {paused}")

    def start(self):
        self.observer.schedule(self.handler, self.local_path, recursive=True)
        self.observer.start()
        print(f"Monitoring started on {self.local_path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
