"""Persistence utilities for Focus Guardian."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

DEFAULT_CONFIG: Dict[str, Any] = {
    "blocked_sites": [
        "youtube.com", "www.youtube.com",
        "reddit.com", "www.reddit.com",
        "tiktok.com", "www.tiktok.com",
        "twitter.com", "x.com",
        "facebook.com", "instagram.com",
        "twitch.tv", "netflix.com"
    ],
    "blocked_apps": [
        "steam.exe", "chrome.exe", "firefox.exe",
        "msedge.exe", "discord.exe"
    ],
    "hard_mode": False,
    "run_on_startup": False,
    "password_hash": None,
    "api_key": "",
}

DEFAULT_SCHEDULE: Dict[str, Any] = {"blocks": []}
DEFAULT_TASKS: Dict[str, Any] = {"tasks": []}
DEFAULT_COMMITMENTS: Dict[str, Any] = {
    "weekly_events": [],
    "preferences": {
        "wake_time": "07:00",
        "sleep_time": "23:00",
        "gym_frequency": 3,
        "focus_block_length": 50,
        "break_length": 10,
        "meals_per_day": 3,
        "morning_routine_length": 30,
        "evening_routine_length": 30,
    },
}
DEFAULT_STATS: Dict[str, Any] = {
    "total_focus_time": 0,
    "sessions_completed": 0,
    "current_streak": 0,
    "longest_streak": 0,
    "last_session_date": None,
}


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    """Load JSON data from *path* returning *default* when unavailable."""
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return dict(default)
    return dict(default)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Persist *data* to *path* in JSON format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def load_application_state(
    config_path: Path,
    schedule_path: Path,
    tasks_path: Path,
    commitments_path: Path,
    stats_path: Path,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Load all persisted application files."""
    config = load_json(config_path, DEFAULT_CONFIG)
    schedule = load_json(schedule_path, DEFAULT_SCHEDULE)
    tasks = load_json(tasks_path, DEFAULT_TASKS)
    commitments = load_json(commitments_path, DEFAULT_COMMITMENTS)
    stats = load_json(stats_path, DEFAULT_STATS)

    prefs = commitments.setdefault("preferences", {})
    prefs.setdefault("morning_routine_length", 30)
    prefs.setdefault("evening_routine_length", 30)

    return config, schedule, tasks, commitments, stats
