"""Block and time conversion helpers."""
from __future__ import annotations

from typing import Tuple

MINUTES_PER_DAY = 24 * 60


def convert_to_12hr(time_24: str) -> str:
    """Convert a 24-hour HH:MM string to 12-hour AM/PM representation."""
    try:
        hour, minute = map(int, time_24.split(":"))
    except Exception:
        return time_24

    period = "AM" if hour < 12 else "PM"
    hour_12 = hour if 1 <= hour <= 12 else hour % 12 or 12
    return f"{hour_12}:{minute:02d} {period}"


def parse_time(value: str) -> int:
    """Return minutes since midnight for a HH:MM string."""
    try:
        hour, minute = map(int, value.split(":"))
        return hour * 60 + minute
    except Exception:
        return 0


def minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to a HH:MM string (24-hour)."""
    try:
        minutes = int(round(minutes)) % MINUTES_PER_DAY
    except Exception:
        return "00:00"
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def normalize_minutes(value: int, wake_minutes: int, sleep_minutes: int, crosses_midnight: bool) -> int:
    """Map a clock value into the scheduling timeline respecting wraparound."""
    if crosses_midnight and value < wake_minutes and value <= sleep_minutes:
        return value + MINUTES_PER_DAY
    return value


def normalize_window(
    start_minutes: int,
    end_minutes: int,
    wake_minutes: int,
    sleep_minutes: int,
    crosses_midnight: bool,
) -> Tuple[int, int]:
    """Normalize a start/end pair into a monotonically increasing window."""
    start = normalize_minutes(start_minutes, wake_minutes, sleep_minutes, crosses_midnight)
    end = normalize_minutes(end_minutes, wake_minutes, sleep_minutes, crosses_midnight)
    if end <= start:
        end += MINUTES_PER_DAY
    return start, end
