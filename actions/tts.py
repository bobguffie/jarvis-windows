"""
TTS (Text-to-Speech) — Linux version (Piper).
Uses Piper TTS for fast, offline text-to-speech output.
Supports NVIDIA GPU acceleration (--use-cuda) with fallback to CPU.
Output via PipeWire (pw-cat) for buffer-free playback.
"""

import os
import re
import time
import json
import struct
import shutil
import subprocess
import threading
import tempfile
from pathlib import Path


# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPER_DIR = os.path.join(BASE_DIR, "piper", "piper")
PIPER_BIN = os.path.join(PIPER_DIR, "piper")
PIPER_MODEL = os.path.join(BASE_DIR, "piper", "en_GB-alan-medium.onnx")
PIPER_MODEL_JSON = os.path.join(BASE_DIR, "piper", "en_GB-alan-medium.onnx.json")


# ── GPU detection (cached) ──────────────────────────────────────────────────
_has_nvidia_gpu: bool | None = None


def _detect_nvidia_gpu() -> bool:
    """Check if an NVIDIA GPU with CUDA is available via nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return False


def _has_cuda_piper() -> bool:
    """Check if the piper binary was compiled with CUDA support."""
    try:
        result = subprocess.run(
            [PIPER_BIN, "--help"],
            capture_output=True, text=True, timeout=5,
        )
        return "--use-cuda" in result.stdout
    except (FileNotFoundError, Exception):
        return False


def _get_piper_flags(output_file: str | None = None) -> list[str]:
    """Return the optimal Piper flags based on available hardware.

    Args:
        output_file: If set, writes WAV to this file instead of stdout.
    """
    global _has_nvidia_gpu
    if _has_nvidia_gpu is None:
        _has_nvidia_gpu = _detect_nvidia_gpu()

    if output_file:
        flags = ["--model", PIPER_MODEL, "--output_file", output_file]
    else:
        flags = ["--model", PIPER_MODEL, "--output-raw"]
    if _has_nvidia_gpu and _has_cuda_piper():
        flags.append("--use-cuda")
    if not os.path.exists(PIPER_MODEL_JSON):
        flags.extend(["--length-scale", "1.0", "--sentence-silence", "0.3"])
    return flags


def _get_audio_player() -> list[str] | None:
    """Return the best available audio player command args, or None."""
    # PipeWire (pw-cat) — modern, buffered, no underruns
    pw_cat = shutil.which("pw-cat")
    if pw_cat:
        return [pw_cat, "-p", "--format=s16le", "--rate=22050", "--channels=1"]
    # PulseAudio (paplay)
    paplay = shutil.which("paplay")
    if paplay:
        return [paplay, "--raw", "--rate=22050", "--format=s16le", "--channels=1"]
    # ALSA (aplay) — last resort
    aplay = shutil.which("aplay")
    if aplay:
        return [aplay, "-r", "22050", "-f", "S16_LE", "-t", "raw"]
    return None


# ── Text cleaning ───────────────────────────────────────────────────────────

def _clean_for_speech(raw: str) -> str:
    """Strip bullet points, dashes, and other non-speech characters from text."""
    cleaned = raw
    # Remove bullet point symbols and special chars
    for ch in ("•", "●", "○", "▸", "▾", "▶", "⏸", "⏻", "⏹", "⛶", "★", "☆"):
        cleaned = cleaned.replace(ch, "")
    # Remove leading/trailing dashes (but keep mid-sentence hyphens)
    cleaned = cleaned.strip("- ")
    # Collapse multiple whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def _split_sentences(text: str) -> list[str]:
    """Split text into individual spoken sentences by . ! ?"""
    parts = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for p in parts:
        p = p.strip()
        if p:
            sentences.append(p)
    return sentences


# ── Main TTS function ───────────────────────────────────────────────────────

_audio_player_cmd: list[str] | None = None


def _get_or_detect_player() -> list[str] | None:
    global _audio_player_cmd
    if _audio_player_cmd is None:
        _audio_player_cmd = _get_audio_player()
    return _audio_player_cmd


def _play_raw_audio(pcm_data: bytes) -> None:
    """Play raw PCM data through the detected audio system."""
    player = _get_or_detect_player()
    if not player:
        return
    try:
        proc = subprocess.Popen(player, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        proc.stdin.write(pcm_data)
        proc.stdin.close()
        proc.wait(timeout=60)
    except Exception:
        pass


def speak_text(text: str, on_done=None, blocking: bool = False):
    """Speak text using Piper TTS with GPU acceleration.

    Each sentence is rendered to a temporary WAV file via Piper's
    --output_file flag. The complete file is then played with pw-play
    (or paplay), ensuring a clean, pre-rendered track with zero crackles.
    """
    if not text or not text.strip():
        if on_done:
            on_done()
        return

    # Clean and split
    cleaned = _clean_for_speech(text)
    sentences = _split_sentences(cleaned)
    if not sentences:
        if on_done:
            on_done()
        return

    def _run():
        try:
            if not os.path.exists(PIPER_BIN) or not os.path.exists(PIPER_MODEL):
                _fallback_pyttsx3(cleaned)
                if on_done:
                    on_done()
                return

            temp_wav_files = []

            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                part = sentence[:300].strip()
                if not part:
                    continue

                # Render each sentence to its own temp WAV file
                try:
                    fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="jarvis_")
                    os.close(fd)
                    flags = _get_piper_flags(output_file=wav_path)
                    proc = subprocess.run(
                        [PIPER_BIN] + flags,
                        input=part.encode("utf-8"),
                        capture_output=True, timeout=30,
                    )
                    if proc.returncode == 0 and os.path.getsize(wav_path) > 44:
                        temp_wav_files.append(wav_path)
                    else:
                        # Remove failed renders
                        try:
                            os.unlink(wav_path)
                        except Exception:
                            pass
                except Exception:
                    continue

            # Play each WAV file sequentially via system audio
            if temp_wav_files:
                for wav_path in temp_wav_files:
                    try:
                        # Use pw-play if available (PipeWire)
                        pw_play = shutil.which("pw-play")
                        if pw_play:
                            subprocess.run(
                                [pw_play, wav_path],
                                timeout=60, stderr=subprocess.DEVNULL,
                            )
                        else:
                            # Fallback: paplay
                            paplay = shutil.which("paplay")
                            if paplay:
                                subprocess.run(
                                    [paplay, wav_path],
                                    timeout=60, stderr=subprocess.DEVNULL,
                                )
                            else:
                                # Last resort: aplay with WAV format
                                subprocess.run(
                                    ["aplay", wav_path],
                                    timeout=60, stderr=subprocess.DEVNULL,
                                )
                    except Exception:
                        pass
                    finally:
                        # Clean up each WAV file after playback
                        try:
                            os.unlink(wav_path)
                        except Exception:
                            pass
            else:
                # Fallback if no WAV files were generated
                _fallback_pyttsx3(cleaned)

        except Exception:
            try:
                _fallback_pyttsx3(cleaned)
            except Exception:
                pass

        if on_done:
            on_done()

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


# ── Fallback ────────────────────────────────────────────────────────────────

def _fallback_pyttsx3(text: str) -> None:
    """Fallback TTS using pyttsx3 if Piper is not available."""
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


# ── Voice listing ───────────────────────────────────────────────────────────

def get_available_voices() -> list[str]:
    """Returns available Piper voices (model files found in the piper directory)."""
    voices = []
    model_dir = os.path.join(BASE_DIR, "piper")
    if os.path.isdir(model_dir):
        for f in os.listdir(model_dir):
            if f.endswith(".onnx") and not f.startswith("."):
                voices.append(f.replace(".onnx", ""))
    return voices if voices else ["en_GB-alan-medium"]