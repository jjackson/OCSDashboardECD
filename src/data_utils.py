"""
Data utilities for handling timestamped data directories
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import constants


def create_timestamped_data_dir() -> Path:
    """Create a new timestamped data directory and return its path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = Path(constants.DATA_DIR)
    timestamped_dir = data_dir / timestamp
    sessions_dir = timestamped_dir / "sessions"
    
    # Create directories
    timestamped_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir.mkdir(exist_ok=True)
    
    return timestamped_dir


def get_latest_data_dir() -> Optional[Path]:
    """Find and return the path to the most recent timestamped data directory"""
    data_dir = Path(constants.DATA_DIR)
    
    if not data_dir.exists():
        return None
    
    # Find all timestamped directories (format: YYYYMMDD_HHMMSS)
    timestamped_dirs = []
    for item in data_dir.iterdir():
        if item.is_dir() and _is_timestamp_format(item.name):
            timestamped_dirs.append(item)
    
    if not timestamped_dirs:
        return None
    
    # Sort by name (which sorts by timestamp due to format)
    timestamped_dirs.sort(key=lambda x: x.name, reverse=True)
    return timestamped_dirs[0]


def get_latest_sessions_dir() -> Optional[Path]:
    """Get the sessions directory from the most recent timestamped data directory"""
    latest_data_dir = get_latest_data_dir()
    if latest_data_dir:
        sessions_dir = latest_data_dir / "sessions"
        if sessions_dir.exists():
            return sessions_dir
    return None

def list_data_directories() -> List[Path]:
    """List all timestamped data directories, sorted by most recent first"""
    data_dir = Path(constants.DATA_DIR)
    
    if not data_dir.exists():
        return []
    
    timestamped_dirs = []
    for item in data_dir.iterdir():
        if item.is_dir() and _is_timestamp_format(item.name):
            timestamped_dirs.append(item)
    
    # Sort by name (which sorts by timestamp due to format)
    timestamped_dirs.sort(key=lambda x: x.name, reverse=True)
    return timestamped_dirs


def cleanup_old_data(keep_count: int = 5) -> int:
    """Keep only the most recent N data directories, delete the rest"""
    data_dirs = list_data_directories()
    
    if len(data_dirs) <= keep_count:
        return 0
    
    dirs_to_delete = data_dirs[keep_count:]
    deleted_count = 0
    
    for dir_to_delete in dirs_to_delete:
        try:
            shutil.rmtree(dir_to_delete)
            print(f"Deleted old data directory: {dir_to_delete.name}")
            deleted_count += 1
        except Exception as e:
            print(f"Warning: Could not delete {dir_to_delete.name}: {e}")
    
    return deleted_count


def _is_timestamp_format(name: str) -> bool:
    """Check if a directory name matches the timestamp format YYYYMMDD_HHMMSS"""
    if len(name) < 15:  # Minimum length for YYYYMMDD_HHMMSS
        return False
    
    # Check for basic timestamp pattern (allowing for _migrated suffix)
    base_name = name.replace("_migrated", "")
    if len(base_name) != 15:
        return False
    
    try:
        # Try to parse as timestamp
        datetime.strptime(base_name, "%Y%m%d_%H%M%S")
        return True
    except ValueError:
        return False


def get_data_directory_info(data_dir: Path) -> dict:
    """Get information about a data directory"""
    sessions_dir = data_dir / "sessions"
    
    info = {
        "name": data_dir.name,
        "path": str(data_dir),
        "exists": data_dir.exists(),
        "sessions_dir_exists": sessions_dir.exists(),
        "session_count": 0,
        "size_mb": 0
    }
    
    if sessions_dir.exists():
        # Count JSON files in sessions directory
        json_files = list(sessions_dir.glob("*.json"))
        info["session_count"] = len(json_files)
        
        # Calculate directory size
        total_size = 0
        for file_path in data_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        info["size_mb"] = round(total_size / (1024 * 1024), 2)
    
    return info


def load_sessions_from_directory(sessions_dir: Path) -> List[dict]:
    """Load all session data from JSON files in a directory"""
    sessions = []
    
    if not sessions_dir.exists():
        return sessions
    
    json_files = list(sessions_dir.glob("session_*.json"))
    print(f"Loading {len(json_files)} session files from {sessions_dir}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                sessions.append(session_data)
        except Exception as e:
            print(f"Warning: Could not load {json_file.name}: {e}")
    
    return sessions


def get_latest_messages_dir() -> Optional[Path]:
    """Get the messages directory from the most recent timestamped data directory"""
    latest_data_dir = get_latest_data_dir()
    if latest_data_dir:
        messages_dir = latest_data_dir / "messages"
        if messages_dir.exists():
            return messages_dir
    return None


def load_messages_from_directory(messages_dir: Path) -> List[dict]:
    """Load all message data from JSON files in a directory"""
    messages = []
    
    if not messages_dir.exists():
        return messages
    
    json_files = list(messages_dir.glob("messages_*.json"))
    print(f"Loading {len(json_files)} message files from {messages_dir}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                message_data = json.load(f)
                messages.append(message_data)
        except Exception as e:
            print(f"Warning: Could not load {json_file.name}: {e}")
    
    return messages


def load_sessions_with_messages() -> tuple[List[dict], List[dict]]:
    """Load both session metadata and message content from the latest data directory"""
    sessions = []
    messages = []
    
    # Load sessions
    sessions_dir = get_latest_sessions_dir()
    if sessions_dir:
        sessions = load_sessions_from_directory(sessions_dir)
    
    # Load messages
    messages_dir = get_latest_messages_dir()
    if messages_dir:
        messages = load_messages_from_directory(messages_dir)
    
    return sessions, messages


def get_latest_data_summary() -> Optional[dict]:
    """Get the download summary from the most recent data directory"""
    latest_dir = get_latest_data_dir()
    if not latest_dir:
        return None
    
    summary_file = latest_dir / "download_summary.json"
    if not summary_file.exists():
        return None
    
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read summary file: {e}")
        return None
