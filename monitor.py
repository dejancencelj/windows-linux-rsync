import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SyncHandler(FileSystemEventHandler):
    def __init__(self, uploader, local_base_path, blacklist=None):
        self.uploader = uploader
        self.local_base_path = local_base_path
        self.blacklist = blacklist if blacklist else []

    def process_event(self, event):
        if event.is_directory:
            return

        # Calculate relative path
        relative_path = os.path.relpath(event.src_path, self.local_base_path)
        
        # Blacklist check
        path_components = relative_path.split(os.sep)
        # Check if any component matches any item in blacklist
        for skip in self.blacklist:
            if skip and skip in path_components:
                return

        print(f"Detected change in: {relative_path}")
        self.uploader.upload_file(event.src_path, relative_path)

    def on_modified(self, event):
        self.process_event(event)

    def on_created(self, event):
        self.process_event(event)
        
    def on_moved(self, event):
        if not event.is_directory:
             # Logic for moved files: Treat as new file creation at dest for simplicity first
             # Ideally we would delete source and upload dest, but syncing deletes is risky if not careful.
             # User asked for "sync", implying mirroring. 
             # For now, let's just upload the new location.
             relative_path = os.path.relpath(event.dest_path, self.local_base_path)
             print(f"File moved to: {relative_path}")
             self.uploader.upload_file(event.dest_path, relative_path)

class Monitor:
    def __init__(self, local_path, uploader, blacklist=None):
        self.local_path = local_path
        self.uploader = uploader
        self.observer = Observer()
        self.handler = SyncHandler(uploader, local_path, blacklist)

    def start(self):
        self.observer.schedule(self.handler, self.local_path, recursive=True)
        self.observer.start()
        print(f"Monitoring started on {self.local_path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
