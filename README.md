# Windows-Linux Sync App

A Python background application that watches a local Git repository on Windows and syncs only files with visible Git changes to a remote Linux server via SSH/SFTP.

> ⚠️ **Git repositories only.** This app only uploads files that appear as changed in `git status`. The local folder must be a Git repository — non-git folders will not sync anything.

## Features

- **Git-Aware Syncing**: Only uploads files with changes visible in `git status` (modified, added, or untracked). Clean, committed, and `.gitignore`d files are never uploaded.
- **Real-time Monitoring**: Uses `watchdog` to detect file changes instantly.
- **Secure Transfer**: Uses `paramiko` for SFTP over SSH.
- **Pageant Support**: Automatically uses your running Pageant agent for SSH authentication — no password storage needed.
- **Multi-Profile Support**: Configure and switch between multiple server/folder profiles.
- **GUI Settings**: Tkinter-based settings window with live status indicators.
- **Git Repo Indicator**: The UI shows a green/red dot indicating whether the selected local folder is a valid Git repository.

## Requirements

- Windows machine with Python installed
- Git installed and available on your system PATH
- Pageant running with your SSH key loaded
- SSH access to the remote Linux server

## Installation

1. **Install Python**: Ensure Python 3.x is installed on your Windows machine.
2. **Install Git**: Download from [git-scm.com](https://git-scm.com) if not already installed.
3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

1. **Start the App**:
   ```powershell
   python main.py
   ```

2. **Configure**:
   - The Settings window opens automatically.
   - Set **Local Path (Git repo)** to your local Git repository folder.
   - Set **Remote Path** to the destination directory on the server.
   - Enter **Server Host**, **Port**, and **Username**.
   - Click **Save & Close**.

3. **Connect**:
   - Click **Connect** in the System Status bar to start syncing.
   - The status indicators show:
     - 🟢/🔴 **SSH Connection** — whether the SFTP connection is active
     - 🟢/🔴 **Folder Monitor** — whether watchdog is actively monitoring
     - 🟢/🔴 **Git Repo** — whether the local path is a valid Git repository

4. **Sync**:
   - Edit files in your Git repo on Windows.
   - Only files that show up in `git status` (modified, new, untracked) are uploaded.
   - Check the **Activity Log** panel for upload events.

## How Git Filtering Works

When a file change is detected by the file watcher:

1. The app checks if the local folder contains a `.git` directory.
   - If **no** `.git` found → upload is suppressed entirely.
2. Runs `git status --porcelain <file>` for the specific changed file.
   - If git reports changes → file is uploaded.
   - If git reports no changes (file is clean or gitignored) → upload is skipped.

This means:
- ✅ Modified tracked files → uploaded
- ✅ New untracked files → uploaded
- ❌ Files unchanged since last commit → not uploaded
- ❌ Files in `.gitignore` → not uploaded
- ❌ Non-git folders → nothing uploaded

## Notes

- Ensure **Pageant** is running with your key loaded before connecting.
- To run without a terminal window, use `pythonw main.py`.
- The **Blacklist** field lets you exclude specific folders (e.g. `node_modules`, `__pycache__`). `.git` is excluded by default.

## Troubleshooting

- **Nothing is uploading**: Check that the local path is a Git repo (Git Repo indicator should be green) and that the files have uncommitted changes visible in `git status`.
- **SSH connection fails**: Verify Pageant is running with your key loaded and check firewall settings for the configured port.
- **Git not found**: Ensure Git is installed and available on your system PATH.

---

## Version & Authors

**Version:** 2026.02.18

**Author:** [DekoHack](https://github.com/dejancencelj)

**Built with:** [Claude Code](https://claude.ai/claude-code) by [Anthropic](https://anthropic.com)
