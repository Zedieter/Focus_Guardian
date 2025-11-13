"""System-level blocking helpers."""
from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Iterable

HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")


def is_admin() -> bool:
    """Return True when running with administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _focus_markers() -> tuple[str, str]:
    return "# FOCUS_GUARDIAN_START", "# FOCUS_GUARDIAN_END"


def apply_blocks(blocked_sites: Iterable[str]) -> None:
    """Append hosts file entries for the provided *blocked_sites*."""
    if not HOSTS_PATH.exists():
        raise FileNotFoundError(str(HOSTS_PATH))

    start_marker, end_marker = _focus_markers()
    content = HOSTS_PATH.read_text(encoding="utf-8", errors="ignore")

    if start_marker in content:
        return

    with HOSTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{start_marker}\n")
        for site in blocked_sites:
            site = site.strip()
            if site:
                handle.write(f"127.0.0.1 {site}\n")
        handle.write(f"{end_marker}\n")


def remove_blocks() -> None:
    """Remove Focus Guardian markers from the hosts file."""
    if not HOSTS_PATH.exists():
        return

    start_marker, end_marker = _focus_markers()
    lines = HOSTS_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()

    cleaned_lines: list[str] = []
    skipping = False
    for line in lines:
        if start_marker in line:
            skipping = True
            continue
        if end_marker in line:
            skipping = False
            continue
        if not skipping:
            cleaned_lines.append(line)

    HOSTS_PATH.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
