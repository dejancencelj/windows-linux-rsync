# Windows-Linux Sync App

A simple Python background application that watches a local folder on Windows and syncs changes to a remote Linux server via SSH/SFTP.

## Features
- **Real-time Monitoring**: Uses `watchdog` to detect file changes/creations.
- **Secure Sync**: Uses `paramiko` for SFTP transfer.
- **Pageant Support**: Automatically uses your running Pageant agent for authentication (no password storage needed).
- **System Tray**: Runs quietly in the background with a system tray icon.

## Installation

1.  **Install Python**: Ensure Python is installed on your Windows machine.
2.  **Install Dependencies**:
    Open a terminal in this folder and run:
    ```powershell
    pip install -r requirements.txt
    ```

## Usage

1.  **Start the App**:
    ```powershell
    python main.py
    ```
2.  **Configure**:
    - Right-click the system tray icon (Blue/Green square).
    - Select **Settings**.
    - Enter your **Local Path** (folder to watch) and **Remote Path** (destination on server).
    - Enter **Host** and **Username**.
    - Click **Save & Restart**.
3.  **Sync**:
    - The app should automatically connect and start watching.
    - Check the terminal output for logs (or see below for running without terminal).

## Notes
- Ensure **Pageant** is running and your key is loaded before starting the app.
- To run completely in background (no terminal), name the file `main.pyw` or run with `pythonw main.py`.

## Troubleshooting
- If it fails to connect, check your Pageant keys.
- Check firewall settings for the configured port.
