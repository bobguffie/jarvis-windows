"""
Calendar — Linux version (Google Calendar API).

Reads events directly from Google Calendar via the official Google Calendar API.
Falls back to local JSON file for events JARVIS creates itself
(via voice commands like "add an event").

Requires credentials.json (Google Cloud OAuth2) in the project root.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import uuid
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration & Paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_CAL_FILE = BASE_DIR / "memory" / "calendar.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
DEFAULT_DURATION_MIN = 60


def _get_google_calendar_service():
    """Authenticate and return Google Calendar API service instance."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not CREDENTIALS_FILE.exists():
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds)


def _evol_events_in_range(start: dt.datetime, end: dt.datetime) -> list[dict]:
    """Fetch events from Google Calendar API for the given range."""
    service = _get_google_calendar_service()
    if not service:
        return []

    try:
        time_min = start.isoformat() + "Z"
        time_max = end.isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        result = []
        for item in events_result.get("items", []):
            start_data = item["start"]
            end_data = item["end"]

            if "dateTime" in start_data:
                start_dt = dt.datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
                end_dt = dt.datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00"))
                all_day = False
            else:
                start_dt = dt.datetime.strptime(start_data["date"], "%Y-%m-%d")
                end_dt = dt.datetime.strptime(end_data["date"], "%Y-%m-%d")
                all_day = True

            result.append({
                "start_ts": int(start_dt.timestamp()),
                "end_ts": int(end_dt.timestamp()),
                "title": item.get("summary", "Unnamed event").strip(),
                "calendar": "Google Calendar",
                "location": item.get("location", "").strip(),
                "all_day": all_day,
                "notes": item.get("description", "").strip(),
            })
        return result
    except Exception:
        return []


# Local JSON Storage
def _load_local() -> list[dict]:
    if not LOCAL_CAL_FILE.exists():
        return []
    try:
        return json.loads(LOCAL_CAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_local(events: list[dict]) -> None:
    LOCAL_CAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_CAL_FILE.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")


def _local_events_in_range(start: dt.datetime, end: dt.datetime, calendar_name: str = "") -> list[dict]:
    s_ts = int(start.timestamp())
    e_ts = int(end.timestamp())
    out = []
    for ev in _load_local():
        try:
            if ev["start_ts"] >= s_ts and ev["start_ts"] <= e_ts:
                if calendar_name and ev.get("calendar", "").lower() != calendar_name.lower():
                    continue
                out.append(ev)
        except Exception:
            continue
    return out


# Public API


def open_desktop_calendar() -> str:
    """Launch the GNOME Calendar desktop application."""
    import subprocess
    try:
        subprocess.Popen(
            ["gnome-calendar"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "Opening the calendar application."
    except Exception as e:
        return f"Could not open the calendar application: {e}"


def get_calendar_events(query: str = "today", limit: int = 6) -> str:
    window = _normalize_query(query)
    limit = max(1, min(60, int(limit or window["default_limit"])))

    events = _evol_events_in_range(window["start"], window["end"])
    events.extend(_local_events_in_range(window["start"], window["end"]))
    events.sort(key=lambda e: (e["start_ts"], e["title"].lower()))

    now = dt.datetime.now()
    today_start_ts = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

    if window["kind"] in {"next", "agenda"}:
        events = [e for e in events if e["end_ts"] >= today_start_ts]

    if not events:
        return window["empty"]

    if window["kind"] == "next":
        return f"Next event: {_format_event_line(events[0], now)}."

    selected = events[:limit]
    header = str(window["header"]).format(count=len(selected))
    lines = [header]
    for ev in selected:
        lines.append(f"- {_format_event_line(ev, now)}")
    return "\n".join(lines)


def add_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str = "",
    notes: str = "",
    location: str = "",
    calendar_name: str = "",
    all_day: bool = False,
) -> str:
    title = (title or "").strip()
    if not title:
        return "An event title is required to add to the calendar."
    start = _parse_iso(start_iso)
    if not start:
        return "A valid start date is required to add to the calendar."
    end = _parse_iso(end_iso) or start + dt.timedelta(minutes=DEFAULT_DURATION_MIN)

    ev = {
        "id": uuid.uuid4().hex,
        "start_ts": int(start.timestamp()),
        "end_ts": int(end.timestamp()),
        "title": title,
        "calendar": calendar_name or "Local",
        "location": location or "",
        "notes": notes or "",
        "all_day": bool(all_day),
    }

    # Also push to Google Calendar if authenticated
    service = _get_google_calendar_service()
    if service:
        try:
            if all_day:
                body = {
                    "summary": title,
                    "location": location,
                    "description": notes,
                    "start": {"date": start.strftime("%Y-%m-%d")},
                    "end": {"date": end.strftime("%Y-%m-%d")},
                }
            else:
                body = {
                    "summary": title,
                    "location": location,
                    "description": notes,
                    "start": {"dateTime": start.isoformat(), "timeZone": "Europe/London"},
                    "end": {"dateTime": end.isoformat(), "timeZone": "Europe/London"},
                }
            service.events().insert(calendarId="primary", body=body).execute()
        except Exception:
            pass

    events = _load_local()
    events.append(ev)
    _save_local(events)

    now = dt.datetime.now()
    return f"Added to calendar: {_format_event_line(ev, now)}."


def delete_calendar_event(
    title: str,
    start_iso: str = "",
    calendar_name: str = "",
    delete_all_matches: bool = False,
) -> str:
    title = (title or "").strip()
    if not title:
        return "An event title is required to delete from the calendar."
    start = _parse_iso(start_iso) if start_iso else None
    now = dt.datetime.now()

    events = _load_local()
    deleted = []
    remaining = []
    for ev in events:
        if ev["title"].strip().lower() != title.lower():
            remaining.append(ev)
            continue
        if start is not None and abs(ev["start_ts"] - int(start.timestamp())) > 60:
            remaining.append(ev)
            continue
        if calendar_name and ev.get("calendar", "").lower() != calendar_name.lower():
            remaining.append(ev)
            continue
        deleted.append(ev)
        if not delete_all_matches:
            remaining.extend(events[events.index(ev) + 1:])
            break
    if not deleted:
        return f"Event titled '{title}' not found."
    _save_local(remaining)
    last = deleted[-1]
    return f"Deleted from calendar: {_format_event_line(last, now)}."


# Query helpers
def _month_start(value: dt.datetime) -> dt.datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value: dt.datetime, months: int) -> dt.datetime:
    total = (value.year * 12 + (value.month - 1)) + months
    year = total // 12
    month = total % 12 + 1
    return value.replace(year=year, month=month, day=1)


def _parse_iso(value: str) -> dt.datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw.replace("Z", "+00:00")
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d",
        "%d.%m.%Y",
    ):
        try:
            return dt.datetime.strptime(raw, fmt)
        except ValueError:
            continue
    try:
        return dt.datetime.fromisoformat(raw)
    except Exception:
        return None


def _normalize_query(query: str) -> dict:
    q = (query or "today").strip().lower()
    now = dt.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    month_match = re.search(r"(\d+)\s*(ay|month|months)", q)
    if any(t in q for t in ("next month", "gelecek ay", "onumuzdeki ay", "onumuzdeki ay")):
        start = _add_months(_month_start(now), 1)
        end = _add_months(start, 1)
        return {"start": start, "end": end, "default_limit": 24, "kind": "next_month", "header": "Found {count} events for next month:", "empty": "No events on the calendar for next month."}
    if "this month" in q or "bu ay" in q:
        start = _month_start(now)
        end = _add_months(start, 1)
        return {"start": start, "end": end, "default_limit": 24, "kind": "this_month", "header": "Found {count} events for this month:", "empty": "No events on the calendar for this month."}
    if month_match:
        months = max(1, min(12, int(month_match.group(1))))
        return {"start": today_start, "end": _add_months(_month_start(now), months), "default_limit": min(60, max(12, months * 12)), "kind": "months", "header": f"Found {{count}} events for the next {months} months:", "empty": f"No events on the calendar for the next {months} months."}
    week_match = re.search(r"(\d+)\s*(hafta|week|weeks)", q)
    if week_match:
        weeks = max(1, min(12, int(week_match.group(1))))
        return {"start": today_start, "end": today_start + dt.timedelta(days=weeks * 7), "default_limit": min(60, max(8, weeks * 8)), "kind": "weeks", "header": f"Found {{count}} events for the next {weeks} weeks:", "empty": f"No events on the calendar for the next {weeks} weeks."}
    day_match = re.search(r"(\d+)\s*(gun|day|days)", q)
    if day_match:
        days = max(1, min(365, int(day_match.group(1))))
        return {"start": today_start, "end": today_start + dt.timedelta(days=days), "default_limit": min(60, max(8, days * 2)), "kind": "days", "header": f"Found {{count}} events for the next {days} days:", "empty": f"No events on the calendar for the next {days} days."}
    if "tomorrow" in q or "yarin" in q or "yarin" in q:
        start = today_start + dt.timedelta(days=1)
        return {"start": start, "end": start + dt.timedelta(days=1), "default_limit": 6, "kind": "tomorrow", "header": "Found {count} events for tomorrow:", "empty": "No events on the calendar for tomorrow."}
    if any(t in q for t in ("week", "hafta", "7 gun")):
        return {"start": today_start, "end": today_start + dt.timedelta(days=7), "default_limit": 10, "kind": "week", "header": "Found {count} events for the next 7 days:", "empty": "No events on the calendar for the next 7 days."}
    if any(t in q for t in ("next", "siradaki", "siradaki", "sonraki")):
        return {"start": now, "end": now + dt.timedelta(days=365), "default_limit": 1, "kind": "next", "header": "", "empty": "Could not find the next calendar event."}
    if any(t in q for t in ("agenda", "ajanda", "upcoming", "yaklasan", "yaklasan")):
        return {"start": now, "end": now + dt.timedelta(days=30), "default_limit": 8, "kind": "agenda", "header": "Found {count} events in your upcoming agenda:", "empty": "No upcoming calendar events."}
    return {"start": today_start, "end": today_start + dt.timedelta(days=1), "default_limit": 6, "kind": "today", "header": "Found {count} events for today:", "empty": "No events on the calendar for today."}


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _day_label(when: dt.datetime, now: dt.datetime) -> str:
    today = now.date()
    target = when.date()
    if target == today:
        return "today"
    if target == today + dt.timedelta(days=1):
        return "tomorrow"
    return f"{when.day} {MONTHS[when.month]} {WEEKDAYS[when.weekday()]}"


def _format_event_line(event: dict, now: dt.datetime) -> str:
    start = dt.datetime.fromtimestamp(event["start_ts"])
    end = dt.datetime.fromtimestamp(event["end_ts"])
    prefix = _day_label(start, now)
    if event.get("all_day"):
        timing = f"{prefix} all day"
    else:
        timing = f"{prefix} {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
    pieces = [f"{timing} - {event['title']}"]
    if event.get("calendar"):
        pieces.append(f"[{event['calendar']}]")
    if event.get("location"):
        pieces.append(f"@ {event['location']}")
    return " ".join(pieces)