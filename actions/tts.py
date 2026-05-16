"""
TTS (Text-to-Speech) — Windows surumu.
Windows SAPI'yi pyttsx3 (varsa) veya PowerShell System.Speech ile kullanir.
"""

import subprocess
import threading


# pyttsx3 ile sesleri once dene; yoksa PowerShell SAPI fallback.
try:
    import pyttsx3  # type: ignore
    _HAS_PYTTSX3 = True
except Exception:
    _HAS_PYTTSX3 = False


# Windows'ta yerlesik Turkce ses (Win10+): "Microsoft Tolga Desktop".
# Yoksa varsayilan ses kullanilir.
VOICE_HINTS = ("tolga", "turkish", "tr-tr")


def _powershell_speak(text: str) -> None:
    # System.Speech.Synthesis.SpeechSynthesizer ile konusur.
    escaped = text.replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "try { $tr = $s.GetInstalledVoices() | Where-Object { "
        "$_.VoiceInfo.Culture.Name -like 'tr*' -or $_.VoiceInfo.Name -like '*Tolga*' } | "
        "Select-Object -First 1; if ($tr) { $s.SelectVoice($tr.VoiceInfo.Name) } } catch {};"
        f"$s.Speak('{escaped}');"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            check=False,
            capture_output=True,
            timeout=60,
        )
    except FileNotFoundError:
        pass


def _pyttsx3_speak(text: str) -> None:
    try:
        engine = pyttsx3.init()
        try:
            voices = engine.getProperty("voices") or []
            for v in voices:
                desc = (getattr(v, "name", "") + " " + getattr(v, "id", "")).lower()
                if any(h in desc for h in VOICE_HINTS):
                    engine.setProperty("voice", v.id)
                    break
        except Exception:
            pass
        engine.say(text)
        engine.runAndWait()
    except Exception:
        _powershell_speak(text)


def speak_text(text: str, on_done=None, blocking: bool = False):
    if not text or not text.strip():
        if on_done:
            on_done()
        return

    max_len = 500
    if len(text) > max_len:
        text = text[:max_len] + "..."

    def _run():
        try:
            if _HAS_PYTTSX3:
                _pyttsx3_speak(text)
            else:
                _powershell_speak(text)
        except Exception:
            pass
        if on_done:
            on_done()

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def get_available_voices() -> list[str]:
    if _HAS_PYTTSX3:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices") or []
            return [getattr(v, "name", "") for v in voices if getattr(v, "name", "")]
        except Exception:
            pass
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Add-Type -AssemblyName System.Speech;"
             "(New-Object System.Speech.Synthesis.SpeechSynthesizer)."
             "GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"],
            capture_output=True, text=True, timeout=10,
        )
        return [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except Exception:
        return []
