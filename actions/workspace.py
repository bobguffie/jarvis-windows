"""
Workspace — Dynamic workspace card for JARVIS.
Provides a hot-swappable dashboard section that displays either:
  - Currently playing media (MPRIS via playerctl, global bus scan)
  - Shared network to-do list (local or network path, auto-detected)

Media tab auto-switches back to "todo" when all players are idle/stopped for >10s.
"""

from __future__ import annotations

import os
import time
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# Smart todo path: use the network share if it exists, otherwise fall back to
# a local file inside the repository so it works out of the box on any machine.
_NETWORK_TODO = Path("/media/medion/Jarvis-shared/todo.txt")
_LOCAL_TODO   = BASE_DIR / "memory" / "todo.txt"

TODO_PATH = _NETWORK_TODO if _NETWORK_TODO.exists() else _LOCAL_TODO

# ── Idle tracking ────────────────────────────────────────────────────────────
_media_last_active_time: float | None = None  # last time we saw a Playing player
_media_last_stopped_lines: list[str] = ["No media player detected."]


def _get_playerctl_output(args: list[str], timeout: int = 3) -> str:
    """Run playerctl with the given args and return stripped stdout."""
    try:
        result = subprocess.run(
            ["playerctl"] + args,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _get_player_metadata(player: str) -> dict:
    """Fetch metadata for a specific player (e.g. 'vlc', 'spotify', 'chrome').

    Uses `playerctl --format` template strings for reliable extraction.
    Falls back to raw filename from `{{xesam:url}}` if title is empty
    (common for VLC playing local files without embedded tags).
    """
    meta = {
        "name": player,
        "title": "",
        "artist": "",
        "status": "stopped",
    }
    # Title via --format template (most reliable across players)
    try:
        title_raw = subprocess.run(
            ["playerctl", "-p", player, "metadata", "--format", "{{title}}"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip()
        meta["title"] = title_raw
    except Exception:
        pass

    # If title is empty, try xesam:title as fallback
    if not meta["title"]:
        try:
            meta["title"] = subprocess.run(
                ["playerctl", "-p", player, "metadata", "xesam:title"],
                capture_output=True, text=True, timeout=3,
            ).stdout.strip()
        except Exception:
            pass

    # If still empty, extract filename from URL (VLC raw files)
    if not meta["title"]:
        try:
            url_raw = subprocess.run(
                ["playerctl", "-p", player, "metadata", "--format", "{{xesam:url}}"],
                capture_output=True, text=True, timeout=3,
            ).stdout.strip()
            if url_raw:
                if url_raw.startswith("file://"):
                    url_raw = url_raw[7:]
                meta["title"] = os.path.basename(url_raw)
                name_no_ext, _ = os.path.splitext(meta["title"])
                if name_no_ext:
                    meta["title"] = name_no_ext
        except Exception:
            pass

    # Artist via --format template
    try:
        artist_raw = subprocess.run(
            ["playerctl", "-p", player, "metadata", "--format", "{{artist}}"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip()
        meta["artist"] = artist_raw if artist_raw and artist_raw != "(null)" else ""
    except Exception:
        pass

    # Fallback to xesam:artist if empty
    if not meta["artist"]:
        try:
            meta["artist"] = subprocess.run(
                ["playerctl", "-p", player, "metadata", "xesam:artist"],
                capture_output=True, text=True, timeout=3,
            ).stdout.strip()
        except Exception:
            pass

    # Status
    try:
        meta["status"] = subprocess.run(
            ["playerctl", "-p", player, "status"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip().lower()
    except Exception:
        pass

    return meta


def _player_display_name(player_id: str) -> str:
    """Convert a playerctl instance name to a friendly display name."""
    base = player_id.split(".")[0]
    return base.capitalize()


def get_now_playing() -> tuple[list[str], bool]:
    """Return (lines, is_active) describing the currently playing media.

    Scans ALL MPRIS players via `playerctl -l`.
    Priority: Playing > Paused. Ignores Stopped.
    `is_active` is True only if a player with status "Playing" was found.

    Updates internal idle timer used by `check_media_idle_timeout()`.
    """
    global _media_last_active_time, _media_last_stopped_lines

    try:
        players_output = _get_playerctl_output(["-l"])
        if not players_output:
            _media_last_stopped_lines = ["No media player detected."]
            return (_media_last_stopped_lines, False)

        player_ids = [p.strip() for p in players_output.split("\n") if p.strip()]
        if not player_ids:
            _media_last_stopped_lines = ["No media player detected."]
            return (_media_last_stopped_lines, False)

        # Fetch metadata for every player
        all_players = [_get_player_metadata(pid) for pid in player_ids]

        # Sort: Playing first, then Paused, drop Stopped
        active = [p for p in all_players if p["status"] != "stopped"]
        if not active:
            # All players are stopped — cache stopped lines
            chosen = all_players[0]
            source = _player_display_name(chosen["name"])
            _media_last_stopped_lines = [f"Source: {source}", "Status: ⏹ Stopped"]
            return (_media_last_stopped_lines, False)

        # Prefer Playing over Paused
        playing = [p for p in active if p["status"] == "playing"]
        chosen = playing[0] if playing else active[0]

        source = _player_display_name(chosen["name"])
        title = chosen.get("title", "")
        artist = chosen.get("artist", "")
        status = chosen.get("status", "unknown")

        status_icon = "▶" if status == "playing" else ("⏸" if status == "paused" else "⏹")
        is_active = (status == "playing")

        lines = [f"Source: {source}"]
        if title:
            display_title = title if len(title) <= 40 else title[:37] + "..."
            lines.append(f"Playing: {display_title}")
        if artist:
            display_artist = artist if len(artist) <= 35 else artist[:32] + "..."
            lines.append(f"Artist: {display_artist}")
        lines.append(f"Status: {status_icon} {status.capitalize()}")

        # Update active timer
        if is_active:
            _media_last_active_time = time.time()
        elif _media_last_active_time is None:
            _media_last_active_time = time.time()  # first seen paused

        _media_last_stopped_lines = lines[:4]
        return (_media_last_stopped_lines, is_active)

    except FileNotFoundError:
        _media_last_stopped_lines = ["playerctl not installed."]
        return (_media_last_stopped_lines, False)
    except subprocess.TimeoutExpired:
        return (["Media query timed out."], False)
    except Exception as e:
        return ([f"Media error: {str(e)[:40]}"], False)


def check_media_idle_timeout(idle_threshold: float = 10.0) -> bool:
    """Return True if media tab has been idle for longer than idle_threshold seconds.

    Scans all currently active MPRIS players. If ANY player is in "Playing" or "Paused"
    state, the idle timer is reset (preventing false timeouts while media is paused).
    Returns True only if ALL players are stopped/closed AND no Playing was seen
    for longer than idle_threshold.
    """
    # First, scan current players — any Playing or Paused resets the timer
    try:
        players_output = _get_playerctl_output(["-l"])
        if players_output:
            for pid in players_output.split("\n"):
                pid = pid.strip()
                if not pid:
                    continue
                try:
                    status = subprocess.run(
                        ["playerctl", "-p", pid, "status"],
                        capture_output=True, text=True, timeout=2,
                    ).stdout.strip().lower()
                    if status in ("playing", "paused"):
                        # Active player found — reset timer and keep media view
                        global _media_last_active_time
                        _media_last_active_time = time.time()
                        return False
                except Exception:
                    continue
    except Exception:
        pass

    # If _media_last_active_time never set, not idle
    if _media_last_active_time is None:
        return False

    # All players are stopped/closed — check elapsed time since last Playing
    return time.time() - _media_last_active_time > idle_threshold


def refresh_workspace() -> str:
    """Force-refresh the workspace data by resetting the idle timer and re-scanning.

    Returns a confirmation message. Call this via voice action or UI button
    to immediately update the workspace card contents.
    """
    global _media_last_active_time
    # Brief re-scan to update cached data
    get_now_playing()
    _media_last_active_time = time.time()
    return "Workspace data refreshed."


# ── Shared To-Do List ────────────────────────────────────────────────────────

def read_todo_list() -> list[str]:
    """Read the first few lines from the shared network to-do list.

    Creates the file with an empty placeholder if it does not exist.
    Returns a list of up to 4 todo items (or a placeholder).
    """
    try:
        if not TODO_PATH.exists():
            TODO_PATH.parent.mkdir(parents=True, exist_ok=True)
            TODO_PATH.write_text("Shared to-do list — edit this file\n", encoding="utf-8")
            return ["Empty — add items to todo.txt"]

        lines = TODO_PATH.read_text(encoding="utf-8").splitlines()
        items = [l.strip() for l in lines if l.strip()]
        if not items:
            return ["No items in to-do list."]
        return items[:4]

    except PermissionError:
        return ["Todo file not accessible."]
    except OSError as e:
        return [f"Todo error: {str(e)[:40]}"]


# ── Tab switching helper ─────────────────────────────────────────────────────

def get_workspace_lines(tab: str) -> list[str]:
    """Return the appropriate lines for the given workspace tab.

    Args:
        tab: "media" or "todo"

    Returns:
        A list of display lines (strings).
    """
    norm = tab.strip().lower()
    if norm == "media":
        lines, _ = get_now_playing()
        return lines
    # Default to todo
    return read_todo_list()