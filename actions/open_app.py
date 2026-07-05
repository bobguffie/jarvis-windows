"""
Open applications — Linux version.
Works via xdg-open, PATH binaries, and xdg-open fallback.
"""

from __future__ import annotations

import os
import shutil
import subprocess


APP_ALIASES = {
    "browser":       "xdg-open http://google.com",
    "chrome":        "google-chrome",
    "google chrome": "google-chrome",
    "firefox":       "firefox",
    "brave":         "brave-browser",
    "opera":         "opera",
    "terminal":      "gnome-terminal",
    "console":       "gnome-terminal",
    "shell":         "gnome-terminal",
    "explorer":      "nautilus",
    "file manager":  "nautilus",
    "files":         "xdg-open .",
    "home":          "xdg-open ~",
    "spotify":       "spotify",
    "vscode":        "code",
    "vs code":       "code",
    "code":          "code",
    "visual studio code": "code",
    "notion":        "notion",
    "slack":         "slack",
    "discord":       "discord",
    "whatsapp":      "xdg-open https://web.whatsapp.com",
    "telegram":      "telegram-desktop",
    "zoom":          "zoom",
    "mail":          "thunderbird",
    "outlook":       "xdg-open https://outlook.live.com",
    "notes":         "gedit",
    "notepad":       "gedit",
    "text editor":   "gedit",
    "music":         "xdg-open https://open.spotify.com",
    "photos":        "eog",
    "image viewer":  "eog",
    "maps":          "xdg-open https://maps.google.com",
    "calculator":    "gnome-calculator",
    "settings":      "gnome-control-center",
    "system settings": "gnome-control-center",
    "task manager":  "gnome-system-monitor",
    "system monitor": "gnome-system-monitor",
    "control panel": "gnome-control-center",
    "preview":       "eog",
    "textedit":      "gedit",
    "figma":         "xdg-open https://figma.com",
    "postman":       "postman",
    "docker":        "docker",
    "steam":         "steam",
    "vlc":           "vlc",
    "libreoffice":   "libreoffice",
    "office":        "libreoffice",
}


# URI/URL prefixes that should be opened with xdg-open
_URI_PREFIXES = (
    "http://", "https://", "mailto:", "tel:", "ftp://",
)


def _xdg_open(target: str) -> bool:
    try:
        subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def open_app(app_name: str) -> str:
    if not app_name:
        return "No application name specified."

    normalized = app_name.lower().strip()
    resolved = APP_ALIASES.get(normalized, app_name)

    # 1. URI scheme (http, https, mailto, etc.)
    if any(resolved.startswith(p) for p in _URI_PREFIXES):
        if _xdg_open(resolved):
            return f"{app_name} opened."

    # 2. If binary is in PATH, open directly
    binary = resolved.split()[0]  # Handle commands like "xdg-open ."
    exe = shutil.which(binary)
    if exe:
        try:
            # Use shell=True for commands with arguments (e.g., "xdg-open .")
            subprocess.Popen(resolved, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"{app_name} opened."
        except Exception:
            pass

    # 3. Fallback to xdg-open
    try:
        subprocess.Popen(["xdg-open", resolved], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"{app_name} opened."
    except Exception as e:
        return f"Could not open '{app_name}': {e}"