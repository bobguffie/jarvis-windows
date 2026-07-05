"""
Reminders — Linux version.
Uses local JSON storage (memory/reminders.json).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_FILE = BASE_DIR / "memory" / "reminders.json"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _try_outlook():
    # Linux: Outlook not available
    return None, None


def _load_local() -> list[dict]:
    if not LOCAL_FILE.exists():
        return []
    try:
        return json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_local(items: list[dict]) -> None:
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_query(query: str) -> tuple[str, int]:
    q = (query or "").strip().lower()
    if any(t in q for t in ("today", "bugun")):
        return "today", 8
    if any(t in q for t in ("overdue", "geciken", "gecmis")):
        return "overdue", 8
    if any(t in q for t in ("next", "siradaki", "sıradaki")):
        return "next", 1
    if any(t in q for t in ("all", "hepsi", "tum", "tüm", "listele")):
        return "all", 10
    return "upcoming", 8


def _normalize_due_iso(due_iso: str) -> tuple[int, bool]:
    raw = (due_iso or "").strip()
    if not raw:
        return 0, False

    candidates = (
        ("%Y-%m-%dT%H:%M:%S", False),
        ("%Y-%m-%dT%H:%M", False),
        ("%Y-%m-%d %H:%M:%S", False),
        ("%Y-%m-%d %H:%M", False),
        ("%d.%m.%Y %H:%M", False),
        ("%Y-%m-%d", True),
        ("%d.%m.%Y", True),
    )
    if raw.endswith("Z"):
        try:
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return int(parsed.timestamp()), False
        except ValueError:
            pass
    for fmt, all_day in candidates:
        try:
            parsed = dt.datetime.strptime(raw, fmt)
            return int(parsed.timestamp()), all_day
        except ValueError:
            continue
    raise ValueError("Reminder date is invalid. Use 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM'.")


def _outlook_list(query_mode: str, limit: int, list_name: str) -> list[dict]:
    # Linux: return empty, use local only
    return []


def _outlook_add(title: str, due_ts: int, notes: str, list_name: str, priority: str, all_day: bool) -> dict | None:
    # Linux: Outlook not available
    return None


def _day_label(when: dt.datetime, now: dt.datetime) -> str:
    today = now.date()
    target = when.date()
    if target == today:
        return "today"
    if target == today + dt.timedelta(days=1):
        return "tomorrow"
    return f"{when.day} {MONTHS[when.month]} {WEEKDAYS[when.weekday()]}"


def _format_due(item: dict, now: dt.datetime) -> str:
    if item.get("due_ts", 0) <= 0:
        return "no due date set"
    due = dt.datetime.fromtimestamp(item["due_ts"])
    if item.get("all_day"):
        return f"{_day_label(due, now)} all day"
    return f"{_day_label(due, now)} {due.strftime('%H:%M')}"


def _format_reminder_line(item: dict, now: dt.datetime) -> str:
    parts = [f"{_format_due(item, now)} - {item['title']}"]
    if item.get("list_name"):
        parts.append(f"[{item['list_name']}]")
    if item.get("priority") == 2:
        parts.append("(high priority)")
    return " ".join(parts)


def get_reminders(query: str = "upcoming", limit: int = 8, list_name: str = "") -> str:
    mode, default_limit = _normalize_query(query)
    limit = max(1, min(20, int(limit or default_limit)))

    items = _outlook_list(mode, limit, list_name)
    items.extend(_load_local())

    now = dt.datetime.now()
    now_ts = int(now.timestamp())
    today_start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    today_end = today_start + 86400

    if mode == "today":
        items = [i for i in items if today_start <= i.get("due_ts", 0) < today_end]
    elif mode == "overdue":
        items = [i for i in items if 0 < i.get("due_ts", 0) < now_ts]
    elif mode == "next":
        items = [i for i in items if i.get("due_ts", 0) >= now_ts]
    elif mode == "upcoming":
        items = [i for i in items if i.get("due_ts", 0) >= now_ts]

    items.sort(key=lambda i: (i.get("due_ts", 0) <= 0, i.get("due_ts", 0), i["title"].lower()))

    if not items:
        if mode == "today":   return "No reminders for today."
        if mode == "overdue": return "No overdue reminders."
        if mode == "next":    return "Could not find the next reminder."
        if mode == "all":     return "No open reminders found."
        return "No upcoming reminders."

    if mode == "next":
        return f"Next reminder: {_format_reminder_line(items[0], now)}."

    items = items[:limit]
    if mode == "today":
        header = f"Found {len(items)} reminders for today:"
    elif mode == "overdue":
        header = f"Found {len(items)} overdue reminders:"
    elif mode == "all":
        header = f"Found {len(items)} open reminders:"
    else:
        header = f"Found {len(items)} upcoming reminders:"

    lines = [header]
    for item in items:
        lines.append(f"- {_format_reminder_line(item, now)}")
    return "\n".join(lines)


def add_reminder(
    title: str,
    due_iso: str = "",
    notes: str = "",
    list_name: str = "",
    priority: str = "",
    all_day: bool = False,
) -> str:
    if not title or not title.strip():
        return "Reminder title cannot be empty."

    due_ts = 0
    all_day_final = bool(all_day)
    if due_iso and due_iso.strip():
        try:
            due_ts, inferred = _normalize_due_iso(due_iso)
        except ValueError as exc:
            return str(exc)
        all_day_final = all_day_final or inferred

    created = _outlook_add(title.strip(), due_ts, notes or "", list_name, priority, all_day_final)
    if created is None:
        prio_map = {"low": 0, "medium": 1, "high": 2}
        created = {
            "id": uuid.uuid4().hex,
            "title": title.strip(),
            "list_name": list_name or "Local",
            "notes": notes or "",
            "priority": prio_map.get((priority or "").lower(), 1),
            "due_ts": due_ts,
            "all_day": all_day_final,
        }
        items = _load_local()
        items.append(created)
        _save_local(items)

    now = dt.datetime.now()
    when = _format_due(created, now)
    list_suffix = f" [{created['list_name']}]" if created.get("list_name") else ""
    return f"Reminder added: {when} - {created['title']}{list_suffix}"