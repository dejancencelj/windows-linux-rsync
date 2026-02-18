import json
import os

CONFIG_FILE = "config.json"

DEFAULT_PROFILE = {
    "name": "Default Profile",
    "local_path": "",
    "remote_path": "",
    "server_host": "",
    "server_port": 22,
    "username": ""
}

DEFAULT_CONFIG = {
    "profiles": [DEFAULT_PROFILE],
    "active_index": 0
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            
        # Migration check: if old config format (no 'profiles' key), migrate it
        if "profiles" not in data:
            migrated_profile = DEFAULT_PROFILE.copy()
            migrated_profile.update(data) # Copy old keys like local_path etc.
            migrated_profile["name"] = "Default Profile"
            new_config = {
                "profiles": [migrated_profile],
                "active_index": 0
            }
            save_config(new_config)
            return new_config
            
        return data
    except Exception:
        return DEFAULT_CONFIG

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

def get_active_profile(config_data):
    """Helper to get the currently active profile dict."""
    try:
        idx = config_data.get("active_index", 0)
        profiles = config_data.get("profiles", [])
        if 0 <= idx < len(profiles):
            return profiles[idx]
    except (IndexError, TypeError):
        pass
    return None
