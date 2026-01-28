import paramiko
import os
import stat

class Uploader:
    def __init__(self, host, port, username, remote_base_path):
        self.host = host
        self.port = port
        self.username = username
        self.remote_base_path = remote_base_path
        self.ssh = None
        self.sftp = None

    def connect(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # allow_agent=True should pick up Pageant on Windows automatically
            self.ssh.connect(self.host, port=self.port, username=self.username, allow_agent=True, look_for_keys=True)
            self.sftp = self.ssh.open_sftp()
            print(f"Connected to {self.host}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def ensure_remote_dir(self, remote_path):
        """Recursively create remote directories if they don't exist."""
        dirs = []
        path = remote_path
        while True:
            try:
                self.sftp.stat(path)
                break
            except FileNotFoundError:
                dirs.append(path)
                path = os.path.dirname(path)
        
        while dirs:
            dir_to_create = dirs.pop()
            try:
                self.sftp.mkdir(dir_to_create)
                print(f"Created remote dir: {dir_to_create}")
            except OSError:
                pass # Already exists

    def upload_file(self, local_path, relative_path):
        if not self.sftp:
            if not self.connect():
                return
        
        remote_file_path = self.remote_base_path.rstrip('/') + '/' + relative_path.replace('\\', '/')
        remote_dir = os.path.dirname(remote_file_path)

        try:
            self.ensure_remote_dir(remote_dir)
            
            # Normalize paths for Windows/Linux strings
            local_path = os.path.abspath(local_path)
            
            print(f"Uploading {local_path} to {remote_file_path}")
            self.sftp.put(local_path, remote_file_path)
            print("Upload successful")
            
        except Exception as e:
            print(f"Failed to upload {local_path}: {e}")
            # Try reconnecting once
            if self.connect():
                 # Retry upload logic (simplified for now)
                 pass

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
