"""
Simple weather summary — works through a remote service.
https://github.com/bnsware

Default location:
- Uses JARVIS_WEATHER_LOCATION env var if set
- Otherwise defaults to Hatay
"""

from __future__ import annotations

import os

import requests


def get_weather_summary(location: str | None = None) -> str:
    target = (location or os.environ.get("JARVIS_WEATHER_LOCATION") or "Hatay").strip()
    try:
        response = requests.get(
            f"https://wttr.in/{target}",
            params={"format": "j1"},
            timeout=10,
            headers={"User-Agent": "JARVIS Windows"},
        )
        response.raise_for_status()
        payload = response.json()
        current = (payload.get("current_condition") or [{}])[0]
        temp_c = current.get("temp_C")
        feels_like = current.get("FeelsLikeC")
        weather_desc = ((current.get("weatherDesc") or [{}])[0]).get("value", "")
        humidity = current.get("humidity")

        parts = []
        if temp_c:
            parts.append(f"{temp_c} degrees")
        if weather_desc:
            parts.append(weather_desc.lower())
        if feels_like and feels_like != temp_c:
            parts.append(f"feels like {feels_like} degrees")
        if humidity:
            parts.append(f"humidity {humidity}%")

        if not parts:
            return "Weather information is currently unavailable."

        return f"Weather for {target}: " + ", ".join(parts) + "."
    except Exception:
        return "Weather information is currently unavailable."
