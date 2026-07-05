"""
TTS (Text-to-Speech) — Linux version (Piper).
Uses Piper TTS for fast, offline text-to-speech output.
"""

import os
import subprocess
import threading


# Paths to the local piper binary and voice model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPER_BIN = os.path.join(BASE_DIR, "piper", "piper", "piper")
PIPER_MODEL = os.path.join(BASE_DIR, "piper", "en_GB-alan-medium.onnx")


def speak_text(text: str, on_done=None, blocking: bool = False):
    if not text or not text.strip():
        if on_done:
            on_done()
        return

    max_len = 500
    if len(text) > max_len:
        text = text[:max_len] + "..."

    # Clean text for shell safety
    safe_text = text.replace('"', '\\"')

    def _run():
        try:
            if os.path.exists(PIPER_BIN) and os.path.exists(PIPER_MODEL):
                cmd = f'echo "{safe_text}" | "{PIPER_BIN}" --model "{PIPER_MODEL}" --output_raw | aplay -r 22050 -f S16_LE -t raw'
                subprocess.run(cmd, shell=True, check=False, timeout=30)
            else:
                # Fallback: try pyttsx3 if Piper is not set up
                _fallback_pyttsx3(text)
        except Exception:
            # Silent fallback
            try:
                _fallback_pyttsx3(text)
            except Exception:
                pass
        if on_done:
            on_done()

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def _fallback_pyttsx3(text: str) -> None:
    """Fallback TTS using pyttsx3 if Piper is not available."""
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def get_available_voices() -> list[str]:
    """Returns available Piper voices (model files found in the piper directory)."""
    voices = []
    model_dir = os.path.join(BASE_DIR, "piper")
    if os.path.isdir(model_dir):
        for f in os.listdir(model_dir):
            if f.endswith(".onnx") and not f.startswith("."):
                voices.append(f.replace(".onnx", ""))
    return voices if voices else ["en_GB-alan-medium"]
