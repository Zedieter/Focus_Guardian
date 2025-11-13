"""Scheduling utilities for Focus Guardian."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from . import blocks, meals


ScheduleEntry = Dict[str, object]


def is_focus_block(block: Dict[str, object]) -> bool:
    block_type = str(block.get("type", "")).lower()
    return block_type in {"focus_block", "focus_placeholder", "focus"}


def is_fixed_block(block: Dict[str, object]) -> bool:
    block_type = str(block.get("type", "")).lower()
    return block_type in {"weekly_event", "meal", "morning_routine", "evening_routine"}


def create_focus_entry(start: int, end: int, title: str = "Focus Block") -> ScheduleEntry:
    block = {
        "type": "focus_block",
        "title": title or "Focus Block",
        "focus_required": True,
    }
    return {"start": start, "end": end, "block": block}


def create_free_time_entry(start: int, end: int, title: str = "Free Time") -> ScheduleEntry:
    block = {
        "type": "freetime",
        "title": title or "Free Time",
        "focus_required": False,
    }
    return {"start": start, "end": end, "block": block}


def build_focus_sequence(start: int, end: int, preferences: Dict[str, object]) -> List[ScheduleEntry]:
    focus_len = max(5, int(preferences.get("focus_block_length", 50)))
    break_len = max(0, int(preferences.get("break_length", 0)))

    segments: List[ScheduleEntry] = []
    cursor = start

    while cursor + focus_len <= end - 1e-6:
        block_end = cursor + focus_len
        segments.append(create_focus_entry(cursor, block_end))
        cursor = block_end

        remaining = end - cursor
        if break_len > 0 and remaining >= break_len + focus_len:
            break_end = cursor + break_len
            segments.append(create_free_time_entry(cursor, break_end))
            cursor = break_end

    if cursor < end - 1e-6:
        segments.append(create_free_time_entry(cursor, end))

    return segments


def fill_gaps_with_focus(
    entries: List[ScheduleEntry],
    day_start: int,
    day_end: int,
    preferences: Dict[str, object],
) -> None:
    entries.sort(key=lambda e: e["start"])
    new_entries: List[ScheduleEntry] = []
    cursor = day_start

    for entry in entries:
        start = max(int(entry["start"]), day_start)
        end = min(int(entry["end"]), day_end)

        if end <= start:
            continue

        if start > cursor:
            new_entries.extend(build_focus_sequence(cursor, start, preferences))
            cursor = start
        else:
            start = max(start, cursor)

        block = entry["block"]
        if is_focus_block(block):
            new_entries.extend(build_focus_sequence(start, end, preferences))
        else:
            entry["start"] = start
            entry["end"] = end
            new_entries.append(entry)

        cursor = max(cursor, end)

    if cursor < day_end:
        new_entries.extend(build_focus_sequence(cursor, day_end, preferences))

    entries[:] = new_entries


def sanitize_filler_blocks(blocks_list: List[Dict[str, object]], tasks: Dict[str, object]) -> None:
    filler_keywords = [
        "free",
        "personal",
        "project",
        "buffer",
        "catch",
        "admin",
        "rest",
        "recovery",
        "flex",
        "exercise",
        "movement",
        "leisure",
        "downtime",
        "placeholder",
        "unwind",
        "relax",
        "misc",
    ]
    protected_types = {
        "meal",
        "weekly_event",
        "morning_routine",
        "evening_routine",
        "freetime",
        "focus_block",
    }

    task_titles = {task.get("name", "").strip().lower() for task in tasks.get("tasks", [])}

    for block in blocks_list:
        block_type = str(block.get("type", "")).lower()
        raw_title = str(block.get("title", "")).strip()
        title_lower = raw_title.lower()

        if block_type in protected_types:
            continue
        if block.get("focus_required"):
            continue
        if block_type.startswith("task") or "todo" in block_type:
            continue
        if "todo" in title_lower or "task" in title_lower:
            continue
        if title_lower in task_titles:
            block["type"] = "todo"
            block.setdefault("focus_required", False)
            continue

        if any(keyword in block_type for keyword in filler_keywords) or any(
            keyword in title_lower for keyword in filler_keywords
        ):
            if "free" in block_type or "free" in title_lower:
                block["type"] = "freetime"
                block["title"] = raw_title or "Free Time"
                block["focus_required"] = False
            else:
                block["type"] = "focus_block"
                block["title"] = "Focus Block"
                block["focus_required"] = True


def normalize_focus_blocks(blocks_list: List[Dict[str, object]], tasks: Dict[str, object]) -> None:
    task_titles = {task.get("name", "").strip().lower() for task in tasks.get("tasks", [])}

    for block in blocks_list:
        block_type = str(block.get("type", "")).lower()
        title = str(block.get("title", "")).strip()
        title_lower = title.lower()

        if block_type == "freetime":
            block["title"] = title or "Free Time"
            block["focus_required"] = False
            continue

        if block_type in {"meal", "weekly_event", "morning_routine", "evening_routine"}:
            block["focus_required"] = False
            if not title:
                defaults = {
                    "meal": "Meal",
                    "weekly_event": "Weekly Event",
                    "morning_routine": "Morning Routine",
                    "evening_routine": "Evening Routine",
                }
                block["title"] = defaults.get(block_type, title)
            continue

        if block_type.startswith("task") or "todo" in block_type:
            block.setdefault("focus_required", False)
            continue

        if title_lower in task_titles or "todo" in title_lower or "task" in title_lower:
            block["type"] = "todo"
            block.setdefault("focus_required", False)
            continue

        block["type"] = "focus_block"
        block["title"] = title or "Focus Block"
        block["focus_required"] = True


def apply_task_duration_constraints(entries: List[ScheduleEntry], tasks: Dict[str, object]) -> None:
    task_map = {}
    for task in tasks.get("tasks", []):
        name = task.get("name", "").strip().lower()
        duration = int(task.get("duration", 0) or 0)
        if name and duration > 0:
            task_map[name] = duration

    if not task_map:
        return

    entries.sort(key=lambda e: e["start"])

    for idx, entry in enumerate(entries):
        block = entry["block"]
        block_type = str(block.get("type", "")).lower()
        title = str(block.get("title", "")).strip().lower()

        if block_type not in {"task", "todo"} and title not in task_map:
            continue

        duration = task_map.get(title)
        if not duration:
            continue

        desired_end = entry["start"] + duration
        if desired_end <= entry["start"]:
            continue

        entry["end"] = desired_end
        current_end = entry["end"]

        for next_idx in range(idx + 1, len(entries)):
            next_entry = entries[next_idx]
            if next_entry["start"] >= current_end:
                break

            overlap = current_end - next_entry["start"]
            if overlap <= 0:
                break

            if is_fixed_block(next_entry["block"]):
                entry["end"] = next_entry["start"]
                current_end = entry["end"]
                break

            next_entry["start"] += overlap
            next_entry["end"] += overlap
            current_end = max(current_end, next_entry["end"])


def insert_fixed_block(entries: List[ScheduleEntry], start: int, end: int, block: Dict[str, object]) -> None:
    if end - start <= 0:
        return

    adjusted_entries: List[ScheduleEntry] = []
    for entry in entries:
        if entry["end"] <= start or entry["start"] >= end:
            adjusted_entries.append(entry)
            continue

        if entry["start"] < start:
            before_block = dict(entry["block"])
            if start - entry["start"] > 0:
                adjusted_entries.append({
                    "start": entry["start"],
                    "end": start,
                    "block": before_block,
                })

        if entry["end"] > end:
            after_block = dict(entry["block"])
            if entry["end"] - end > 0:
                adjusted_entries.append({
                    "start": end,
                    "end": entry["end"],
                    "block": after_block,
                })

    block_copy = dict(block)
    adjusted_entries.append({"start": start, "end": end, "block": block_copy})
    entries[:] = sorted(adjusted_entries, key=lambda e: e["start"])


def ensure_routines(entries: List[ScheduleEntry], day_start: int, day_end: int, preferences: Dict[str, object]) -> None:
    total_window = max(day_end - day_start, 0)
    if total_window <= 0:
        entries.clear()
        return

    morning_pref = preferences.get("morning_routine_length", 30) or 30
    evening_pref = preferences.get("evening_routine_length", 30) or 30
    morning_len = max(1, int(morning_pref))
    evening_len = max(1, int(evening_pref))

    if morning_len + evening_len > total_window:
        scale = total_window / float(morning_len + evening_len)
        morning_len = max(1, int(round(morning_len * scale)))
        evening_len = max(1, int(round(evening_len * scale)))

    if morning_len + evening_len > total_window:
        overflow = morning_len + evening_len - total_window
        reduce_evening = min(overflow, max(0, evening_len - 1))
        evening_len -= reduce_evening
        overflow -= reduce_evening
        if overflow > 0 and morning_len > 1:
            morning_len -= min(overflow, morning_len - 1)

    morning_end = min(day_start + morning_len, day_end)
    if day_end - morning_end < 1 and day_end - day_start >= 1:
        morning_end = max(day_start, day_end - 1)

    remaining_after_morning = max(day_end - morning_end, 0)
    if remaining_after_morning >= 1:
        evening_len = max(1, min(evening_len, remaining_after_morning))
    else:
        evening_len = 0
    evening_start = day_end - evening_len

    if evening_start < morning_end:
        evening_start = morning_end

    entries[:] = [
        entry
        for entry in entries
        if str(entry["block"].get("type", "")).lower() not in {"morning_routine", "evening_routine"}
    ]

    if morning_end > day_start:
        morning_block = {
            "type": "morning_routine",
            "title": "Morning Routine",
            "focus_required": False,
        }
        insert_fixed_block(entries, day_start, morning_end, morning_block)

    if evening_start < day_end:
        evening_block = {
            "type": "evening_routine",
            "title": "Evening Routine",
            "focus_required": False,
        }
        insert_fixed_block(entries, evening_start, day_end, evening_block)


def enforce_weekly_events(
    entries: List[ScheduleEntry],
    todays_events: Sequence[Dict[str, object]],
    day_start: int,
    day_end: int,
    wake_minutes: int,
    sleep_minutes: int,
    crosses_midnight: bool,
) -> None:
    if not todays_events:
        return

    for event in todays_events:
        try:
            raw_start = blocks.parse_time(event["start"])
            raw_end = blocks.parse_time(event["end"])
        except Exception:
            continue

        title = event.get("title") or "Weekly Event"
        event_start, event_end = blocks.normalize_window(
            raw_start, raw_end, wake_minutes, sleep_minutes, crosses_midnight
        )

        event_start = max(day_start, event_start)
        event_end = min(day_end, event_end)

        if event_end - event_start < 5:
            continue

        adjusted_entries: List[ScheduleEntry] = []
        for entry in entries:
            if entry["end"] <= event_start or entry["start"] >= event_end:
                adjusted_entries.append(entry)
                continue

            if entry["start"] < event_start:
                before_block = dict(entry["block"])
                adjusted_entries.append({
                    "start": entry["start"],
                    "end": event_start,
                    "block": before_block,
                })

            if entry["end"] > event_end:
                after_block = dict(entry["block"])
                adjusted_entries.append({
                    "start": event_end,
                    "end": entry["end"],
                    "block": after_block,
                })

        event_block = {
            "type": "weekly_event",
            "title": title,
            "focus_required": False,
            "start": blocks.minutes_to_time(event_start),
            "end": blocks.minutes_to_time(event_end),
        }
        adjusted_entries.append({"start": event_start, "end": event_end, "block": event_block})
        entries[:] = sorted(adjusted_entries, key=lambda e: e["start"])


def post_process_schedule(
    schedule: Dict[str, object],
    commitments: Dict[str, object],
    tasks: Dict[str, object],
    meals_count: int,
    todays_events: Optional[Sequence[Dict[str, object]]] = None,
) -> List[Dict[str, object]]:
    todays_events = list(todays_events or [])
    preferences = commitments.get("preferences", {})
    wake_time = preferences.get("wake_time", "07:00")
    sleep_time = preferences.get("sleep_time", "23:00")
    wake_minutes = blocks.parse_time(wake_time)
    sleep_minutes = blocks.parse_time(sleep_time)

    day_start = wake_minutes
    day_end = sleep_minutes
    crosses_midnight = False

    if day_end <= day_start:
        day_end += blocks.MINUTES_PER_DAY
        crosses_midnight = True

    if todays_events:
        earliest = day_start
        latest = day_end
        for event in todays_events:
            try:
                raw_start = blocks.parse_time(event["start"])
                raw_end = blocks.parse_time(event["end"])
            except Exception:
                continue

            event_start, event_end = blocks.normalize_window(
                raw_start, raw_end, wake_minutes, sleep_minutes, crosses_midnight
            )
            earliest = min(earliest, event_start)
            latest = max(latest, event_end)

        day_start = min(day_start, earliest)
        day_end = max(day_end, latest)

    raw_blocks = schedule.get("blocks", [])
    entries: List[ScheduleEntry] = []

    for block in raw_blocks:
        try:
            raw_start = blocks.parse_time(block["start"])
            raw_end = blocks.parse_time(block["end"])
        except Exception:
            continue

        start, end = blocks.normalize_window(
            raw_start, raw_end, wake_minutes, sleep_minutes, crosses_midnight
        )

        start_clamped = max(start, day_start)
        end_clamped = min(end, day_end)

        if end_clamped - start_clamped < 1:
            continue

        block_copy = dict(block)
        entries.append({"start": start_clamped, "end": end_clamped, "block": block_copy})

    entries.sort(key=lambda e: e["start"])

    enforce_weekly_events(entries, todays_events, day_start, day_end, wake_minutes, sleep_minutes, crosses_midnight)
    ensure_routines(entries, day_start, day_end, preferences)
    apply_task_duration_constraints(entries, tasks)
    meals.ensure_meal_coverage(entries, meals_count, day_start, day_end)
    fill_gaps_with_focus(entries, day_start, day_end, preferences)

    entries.sort(key=lambda e: e["start"])
    new_blocks: List[Dict[str, object]] = []
    for entry in entries:
        block = entry["block"]
        block["start"] = blocks.minutes_to_time(int(entry["start"]))
        block["end"] = blocks.minutes_to_time(int(entry["end"]))
        new_blocks.append(block)

    sanitize_filler_blocks(new_blocks, tasks)
    normalize_focus_blocks(new_blocks, tasks)
    return new_blocks
