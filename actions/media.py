"""
Media playback — Linux version.
- Spotify: opens via xdg-open (spotify: URI scheme) or web.
- YouTube: plays in browser.
- Apple Music: opens web page.
- Media control keys via playerctl.
"""

from __future__ import annotations

import os
import subprocess
import urllib.parse

from actions.browser import browser_control


def _play_youtube(query: str) -> str:
    return browser_control("play_youtube", query=query)


def _play_spotify(query: str, autoplay: bool = True) -> str:
    # Try to open Spotify via URI scheme
    encoded_query = urllib.parse.quote(query.strip())
    search_uri = f"spotify:search:{encoded_query}"

    try:
        subprocess.Popen(["xdg-open", search_uri])
    except Exception as exc:
        return f"Could not open Spotify: {exc}"

    if autoplay:
        # Use playerctl to play if Spotify is already running
        try:
            subprocess.run(["playerctl", "next"], check=False, timeout=2)
            return f"Playing on Spotify: {query}"
        except Exception:
            pass

    return f"Spotify search opened for '{query}'."


def _play_apple_music_web(query: str) -> str:
    encoded = urllib.parse.quote(query.strip())
    url = f"https://music.apple.com/search?term={encoded}"
    return browser_control("open_url", url=url)


def media_control(action: str) -> str:
    """
    Controls media playback using playerctl.
    Actions: play_pause, next, previous, stop, play, pause
    """
    mapping = {
        "play_pause": ["playerctl", "play-pause"],
        "next": ["playerctl", "next"],
        "next_track": ["playerctl", "next"],
        "previous": ["playerctl", "previous"],
        "prev": ["playerctl", "previous"],
        "stop": ["playerctl", "stop"],
        "play": ["playerctl", "play"],
        "pause": ["playerctl", "pause"],
    }
    cmd = mapping.get(action.lower())
    if not cmd:
        return f"Unknown media action: {action}. Use: play_pause, next, previous, stop, play, pause."

    try:
        subprocess.run(cmd, check=True, timeout=5)
        return f"Media action '{action}' executed."
    except subprocess.TimeoutExpired:
        return f"Media action '{action}' timed out."
    except FileNotFoundError:
        return "playerctl is not installed. Run: sudo apt install playerctl"
    except Exception as e:
        return f"Failed to execute '{action}': {e}"


def play_media(query: str, provider: str = "auto", autoplay: bool = True) -> str:
    if not query or not query.strip():
        return "No content specified to play."

    normalized_provider = (provider or "auto").strip().lower()
    if normalized_provider in {"yt", "youtube music"}:
        normalized_provider = "youtube"
    elif normalized_provider in {"apple music", "music", "apple_music"}:
        normalized_provider = "apple_music"

    if normalized_provider == "spotify":
        return _play_spotify(query, autoplay=autoplay)
    if normalized_provider == "apple_music":
        return _play_apple_music_web(query)
    if normalized_provider == "youtube":
        return _play_youtube(query)

    # auto: prefer Spotify if installed, otherwise YouTube
    try:
        spotify_check = subprocess.run(["which", "spotify"], capture_output=True, check=False)
        if spotify_check.returncode == 0:
            result = _play_spotify(query, autoplay=autoplay)
            if "Could not open" not in result:
                return result
    except Exception:
        pass

    return _play_youtube(query)