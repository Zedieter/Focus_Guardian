"""Meal placement utilities."""
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from . import blocks


def get_expected_meal_titles(meals_count: int) -> List[str]:
    mapping = {
        1: ["Main Meal"],
        2: ["Breakfast", "Dinner"],
        3: ["Breakfast", "Lunch", "Dinner"],
        4: ["Breakfast", "Snack/Brunch", "Lunch", "Dinner"],
        5: [
            "Breakfast",
            "Mid-morning Snack",
            "Lunch",
            "Afternoon Snack",
            "Dinner",
        ],
        6: [
            "Breakfast",
            "Mid-morning Snack",
            "Lunch",
            "Afternoon Snack",
            "Dinner",
            "Evening Snack",
        ],
    }
    if meals_count in mapping:
        return list(mapping[meals_count])
    return [f"Meal {i + 1}" for i in range(max(meals_count, 0))]


def get_meal_ratios(meals_count: int) -> List[float]:
    ratio_map = {
        1: [0.5],
        2: [0.05, 0.75],
        3: [0.05, 0.5, 0.82],
        4: [0.04, 0.25, 0.55, 0.82],
        5: [0.04, 0.22, 0.45, 0.68, 0.88],
        6: [0.04, 0.2, 0.38, 0.58, 0.78, 0.9],
    }
    if meals_count in ratio_map:
        return list(ratio_map[meals_count])
    if meals_count <= 0:
        return []
    step = 0.85 / max(meals_count - 1, 1)
    return [min(0.9, i * step) for i in range(meals_count)]


def calculate_meal_target(index: int, total: int, day_start: int, day_end: int) -> int:
    if total <= 0:
        return day_start
    ratios = get_meal_ratios(total)
    ratio = ratios[index] if index < len(ratios) else index / max(total - 1, 1)
    ratio = max(0.0, min(ratio, 0.95))
    span = max(day_end - day_start, 1)
    target = day_start + int(span * ratio)
    target = max(day_start, min(target, day_end - 30))
    return target - (target % 5)


def violates_meal_spacing(
    entries: List[dict],
    start: int,
    end: int,
    min_gap: int,
    ignore_entry: Optional[dict] = None,
) -> bool:
    if min_gap <= 0:
        return False
    for entry in entries:
        if entry is ignore_entry:
            continue
        if entry["end"] <= start:
            if start - entry["end"] < min_gap:
                return True
        elif entry["start"] >= end:
            if entry["start"] - end < min_gap:
                return True
        else:
            return True
    return False


def compute_free_segments(entries: Iterable[dict], day_start: int, day_end: int) -> List[Tuple[int, int]]:
    segments: List[Tuple[int, int]] = []
    cursor = day_start
    for entry in sorted(entries, key=lambda e: e["start"]):
        if entry["start"] - cursor >= 20:
            segments.append((cursor, entry["start"]))
        cursor = max(cursor, entry["end"])
    if day_end - cursor >= 20:
        segments.append((cursor, day_end))
    return segments


def insert_meal_entry(
    entries: List[dict],
    target: int,
    title: str,
    day_start: int,
    day_end: int,
    min_gap: int = 30,
    allow_focus_override: bool = False,
) -> Optional[dict]:
    if day_end - day_start < 20:
        return None

    segments = compute_free_segments(entries, day_start, day_end)
    best_candidate: Optional[Tuple[int, int]] = None
    best_distance: Optional[int] = None

    for seg_start, seg_end in segments:
        if seg_end - seg_start < 20:
            continue
        placement_start = max(seg_start, min(target, seg_end - 30))
        placement_start -= placement_start % 5
        placement_end = placement_start + 30
        if placement_end > seg_end:
            placement_end = seg_end
            placement_start = max(seg_start, placement_end - 30)
        if placement_end - placement_start < 20:
            continue
        if violates_meal_spacing(entries, placement_start, placement_end, min_gap):
            continue
        distance = abs(placement_start - target)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_candidate = (placement_start, placement_end)

    if best_candidate:
        meal_block = {
            "start": blocks.minutes_to_time(best_candidate[0]),
            "end": blocks.minutes_to_time(best_candidate[1]),
            "type": "meal",
            "title": title,
            "focus_required": False,
        }
        entry = {"start": best_candidate[0], "end": best_candidate[1], "block": meal_block}
        entries.append(entry)
        entries.sort(key=lambda e: e["start"])
        return entry

    filler_candidates = sorted(enumerate(entries), key=lambda item: item[1]["start"])
    keywords = [
        "free",
        "rest",
        "buffer",
        "flex",
        "break",
        "personal",
        "catch",
        "admin",
        "exercise",
        "transition",
        "placeholder",
    ]

    for idx, entry in filler_candidates:
        block = entry["block"]
        block_type = (block.get("type") or "").lower()
        if block_type in {"weekly_event", "meal"}:
            continue
        if block.get("focus_required") and not allow_focus_override:
            continue
        convertible = any(keyword in block_type for keyword in keywords)
        if not convertible and not allow_focus_override:
            continue
        duration = entry["end"] - entry["start"]
        if duration < 30:
            continue

        meal_start = max(entry["start"], min(target, entry["end"] - 30))
        meal_start -= meal_start % 5
        meal_end = meal_start + 30
        if meal_end > entry["end"]:
            meal_end = entry["end"]
            meal_start = max(entry["start"], meal_end - 30)
        if meal_end - meal_start < 20:
            continue
        if violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
            continue

        base_block = entry["block"]
        new_entries = []

        if meal_start - entry["start"] >= 5:
            before_block = dict(base_block)
            before_block["start"] = blocks.minutes_to_time(entry["start"])
            before_block["end"] = blocks.minutes_to_time(meal_start)
            new_entries.append({"start": entry["start"], "end": meal_start, "block": before_block})

        meal_block = {
            "start": blocks.minutes_to_time(meal_start),
            "end": blocks.minutes_to_time(meal_end),
            "type": "meal",
            "title": title,
            "focus_required": False,
        }
        meal_entry = {"start": meal_start, "end": meal_end, "block": meal_block}
        new_entries.append(meal_entry)

        if entry["end"] - meal_end >= 5:
            after_block = dict(base_block)
            after_block["start"] = blocks.minutes_to_time(meal_end)
            after_block["end"] = blocks.minutes_to_time(entry["end"])
            new_entries.append({"start": meal_end, "end": entry["end"], "block": after_block})

        entries.pop(idx)
        for offset, new_entry in enumerate(new_entries):
            entries.insert(idx + offset, new_entry)
        entries.sort(key=lambda e: e["start"])
        return meal_entry

    candidate_blocks = [
        (abs(((entry["start"] + entry["end"]) / 2) - target), idx, entry)
        for idx, entry in enumerate(entries)
        if (entry["block"].get("type") or "").lower() not in {"weekly_event", "meal"}
        and (allow_focus_override or not entry["block"].get("focus_required"))
    ]
    candidate_blocks.sort(key=lambda item: item[0])

    for _, idx, entry in candidate_blocks:
        start = entry["start"]
        end = entry["end"]
        if end - start < 20:
            continue
        meal_start = max(start, min(target, end - 25))
        meal_start -= meal_start % 5
        meal_end = meal_start + 30
        if meal_end > end:
            meal_end = end
            meal_start = max(start, meal_end - 30)
        if meal_end - meal_start < 20:
            continue
        if violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
            continue

        base_block = entry["block"]
        entries.pop(idx)
        new_entries = []

        if meal_start - start >= 5:
            before_block = dict(base_block)
            before_block["start"] = blocks.minutes_to_time(start)
            before_block["end"] = blocks.minutes_to_time(meal_start)
            new_entries.append({"start": start, "end": meal_start, "block": before_block})

        meal_block = {
            "start": blocks.minutes_to_time(meal_start),
            "end": blocks.minutes_to_time(meal_end),
            "type": "meal",
            "title": title,
            "focus_required": False,
        }
        meal_entry = {"start": meal_start, "end": meal_end, "block": meal_block}
        new_entries.append(meal_entry)

        if end - meal_end >= 5:
            after_block = dict(base_block)
            after_block["start"] = blocks.minutes_to_time(meal_end)
            after_block["end"] = blocks.minutes_to_time(end)
            new_entries.append({"start": meal_end, "end": end, "block": after_block})

        for offset, new_entry in enumerate(new_entries):
            entries.insert(idx + offset, new_entry)
        entries.sort(key=lambda e: e["start"])
        return meal_entry

    return None


def ensure_meal_coverage(entries: List[dict], meals_count: int, day_start: int, day_end: int) -> None:
    if meals_count <= 0:
        entries[:] = [e for e in entries if (e["block"].get("type") or "").lower() != "meal"]
        return

    entries.sort(key=lambda e: e["start"])
    entries[:] = [
        entry for entry in entries if (entry["block"].get("type") or "").lower() != "meal"
    ]
    expected_titles = get_expected_meal_titles(meals_count)

    for idx, title in enumerate(expected_titles):
        target = calculate_meal_target(idx, len(expected_titles), day_start, day_end)
        inserted = insert_meal_entry(entries, target, title, day_start, day_end, min_gap=35)
        if not inserted:
            inserted = insert_meal_entry(entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=True)
        if not inserted:
            inserted = insert_meal_entry(entries, target, title, day_start, day_end, min_gap=25, allow_focus_override=True)
        if not inserted:
            insert_meal_entry(entries, target, title, day_start, day_end, min_gap=20, allow_focus_override=True)

    entries.sort(key=lambda e: e["start"])
    meal_entries = [e for e in entries if (e["block"].get("type") or "").lower() == "meal"]
    meal_entries.sort(key=lambda e: e["start"])

    if len(meal_entries) > len(expected_titles):
        for extra in meal_entries[len(expected_titles):]:
            extra_block = extra["block"]
            extra_block["type"] = "focus_block"
            extra_block["title"] = "Focus Block"
            extra_block["focus_required"] = True

    meal_entries = [e for e in entries if (e["block"].get("type") or "").lower() == "meal"]
    meal_entries.sort(key=lambda e: e["start"])

    for idx, entry in enumerate(meal_entries):
        if idx >= len(expected_titles):
            break
        entry_block = entry["block"]
        entry_block["title"] = expected_titles[idx]
        entry_block["type"] = "meal"
        entry_block["focus_required"] = False
