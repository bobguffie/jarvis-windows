"""
Ekran analizi — Windows surumu.
Aktif pencerenin ekran goruntusunu Windows API (ctypes + PIL) ile alir,
sonra secili backend'e gore Gemini Vision veya LM Studio (OpenAI-uyumlu
vision modeli) ile analiz eder.
"""

from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes as wt
import io
import json
import mimetypes
import tempfile
import time
from pathlib import Path

import requests
from PIL import Image, ImageGrab, ImageStat

from app_config import get_app_config_value, is_local_backend


VISION_MODELS = (
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
)
VISION_MAX_DIMENSION = 1800
VISION_MAX_INLINE_BYTES = 5_500_000


def _screen_permission_message() -> str:
    return (
        "Ekran goruntusu alinamadi. Windows'ta yonetici izni veya korumali "
        "icerik kisitlamasi olabilir. JARVIS'i normal kullanici hesabinda "
        "calistirdigindan ve hedef pencerenin DRM korumali olmadigindan emin ol."
    )


def _get_foreground_window_rect() -> tuple[tuple[int, int, int, int] | None, str, str]:
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, "", ""

    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    window_title = buf.value or ""

    owner = ""
    try:
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            import psutil
            proc = psutil.Process(pid.value)
            owner = proc.name()
        except Exception:
            owner = ""
    except Exception:
        owner = ""

    try:
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        rect = wt.RECT()
        hr = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wt.HWND(hwnd),
            ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if hr == 0:
            return (rect.left, rect.top, rect.right, rect.bottom), owner, window_title
    except Exception:
        pass

    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom), owner, window_title


def _capture_active_window() -> tuple[bool, str, dict]:
    try:
        bbox, owner, title = _get_foreground_window_rect()
        if not bbox:
            return False, "Aktif pencere bulunamadi.", {}
        left, top, right, bottom = bbox
        if right - left <= 4 or bottom - top <= 4:
            image = ImageGrab.grab(all_screens=True)
        else:
            try:
                image = ImageGrab.grab(bbox=bbox, all_screens=True)
            except TypeError:
                image = ImageGrab.grab(bbox=bbox)

        tmp = tempfile.NamedTemporaryFile(prefix="jarvis-screen-", suffix=".png", delete=False)
        tmp.close()
        image.save(tmp.name, format="PNG")
        return True, "", {
            "image_path": tmp.name,
            "owner_name": owner,
            "window_title": title,
            "bounds": {"left": left, "top": top, "right": right, "bottom": bottom},
        }
    except Exception as exc:
        return False, f"Ekran goruntusu alinamadi: {exc}", {}


def _image_looks_blank(image_path: Path) -> bool:
    try:
        with Image.open(image_path) as img:
            sample = img.convert("RGB")
            stat = ImageStat.Stat(sample)
            means = stat.mean
            extrema = stat.extrema
            max_seen = max(channel[1] for channel in extrema)
            mean_total = sum(means) / max(1, len(means))
            return max_seen <= 8 or mean_total <= 3
    except Exception:
        return False


def _prepare_image_bytes(image_path: Path) -> tuple[bytes, str]:
    """Goruntuyu uygun boyuta indirir ve (bytes, mime) doner."""
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/png"
    try:
        with Image.open(image_path) as img:
            work = img.copy()
        if work.mode not in {"RGB", "L"}:
            work = work.convert("RGB")
        if max(work.size) > VISION_MAX_DIMENSION:
            work.thumbnail((VISION_MAX_DIMENSION, VISION_MAX_DIMENSION), Image.Resampling.LANCZOS)
        png_buffer = io.BytesIO()
        work.save(png_buffer, format="PNG", optimize=True)
        png_bytes = png_buffer.getvalue()
        if len(png_bytes) <= VISION_MAX_INLINE_BYTES:
            return png_bytes, "image/png"
        jpg_buffer = io.BytesIO()
        rgb = work.convert("RGB") if work.mode != "RGB" else work
        rgb.save(jpg_buffer, format="JPEG", quality=88, optimize=True)
        return jpg_buffer.getvalue(), "image/jpeg"
    except Exception:
        return image_path.read_bytes(), mime_type


def _vision_prompt(query: str, owner_name: str, window_title: str) -> str:
    label = window_title or owner_name or "aktif pencere"
    user_query = (query or "Ekranda ne var?").strip()
    return (
        "Sen Windows uzerinde JARVIS icin ekran analizi yapan bir goruntu yorumlayicisisin.\n"
        "Asagidaki ekran goruntusu aktif pencereye ait.\n"
        f"Pencere baglami: {label}\n\n"
        "Gorevlerin:\n"
        "1. Pencerenin genel amacini 1-2 cumlede acikla.\n"
        "2. Gorunen onemli metinleri, hata mesajlarini, butonlari, basliklari ve durum etiketlerini oku.\n"
        "3. Kullanici sorusunu bu goruntuye gore dogrudan cevapla.\n"
        "4. Eger bir hata, uyari veya dikkat edilmesi gereken bir sey varsa bunu ayri ve net belirt.\n"
        "5. Uydurma yapma. Emin olmadigin kisimlarda bunu soyle.\n\n"
        f"Kullanici sorusu: {user_query}\n\n"
        "Yaniti Turkce ver. Gereksiz uzun olma, ama okunabilir detay ver."
    )


# ── Gemini backend ───────────────────────────────────────────────────────────

def _extract_gemini_text(response) -> str:
    text = str(getattr(response, "text", "") or "").strip()
    if text:
        return text
    candidates = getattr(response, "candidates", None) or []
    chunks: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = str(getattr(part, "text", "") or "").strip()
            if part_text:
                chunks.append(part_text)
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def _is_transient_vision_error(exc: Exception) -> bool:
    try:
        from google.genai import errors as genai_errors  # type: ignore
        if isinstance(exc, genai_errors.ServerError):
            return True
    except Exception:
        pass
    if isinstance(exc, TimeoutError):
        return True
    message = str(exc or "").lower()
    transient_markers = (
        "503", "429", "deadline", "timed out", "timeout", "unavailable",
        "temporarily unavailable", "service unavailable", "internal error",
        "busy", "overloaded", "resource exhausted", "try again later",
        "backend error", "connection reset",
    )
    return any(marker in message for marker in transient_markers)


def _is_quota_vision_error(exc: Exception) -> bool:
    message = str(exc or "").lower()
    return any(m in message for m in (
        "quota", "rate limit", "resource exhausted",
        "too many requests", "quota exceeded", "limit exceeded", "billing",
    ))


def _friendly_vision_error(exc: Exception) -> str:
    if _is_quota_vision_error(exc):
        return "Vision istegi kota veya hiz limitine takildi. Biraz bekleyip tekrar dene."
    if _is_transient_vision_error(exc):
        return "Vision servisi su anda yogun veya gecici olarak ulasilamiyor. Biraz sonra tekrar dene."
    return f"Vision istegi basarisiz oldu: {exc}"


def _analyze_with_gemini(query: str, image_path: Path, owner_name: str, window_title: str) -> str:
    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not api_key:
        return "Gemini API anahtari eksik oldugu icin ekran analizi yapilamadi."

    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except Exception as exc:
        return f"Gemini SDK yuklenemedi: {exc}"

    prompt = _vision_prompt(query, owner_name, window_title)
    client = genai.Client(api_key=api_key)
    img_bytes, mime = _prepare_image_bytes(image_path)
    image_part = types.Part.from_bytes(data=img_bytes, mime_type=mime)
    retry_delays = (0.9, 1.8, 3.0)
    last_error: Exception | None = None

    for model_name in VISION_MODELS:
        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_text(text=prompt),
                        image_part,
                    ],
                    config=types.GenerateContentConfig(temperature=0.2),
                )
                merged = _extract_gemini_text(response)
                if merged:
                    return merged
                raise RuntimeError("Gemini gecerli bir ekran analizi metni dondurmedi.")
            except Exception as exc:
                last_error = exc
                if attempt < len(retry_delays) and _is_transient_vision_error(exc):
                    time.sleep(delay)
                    continue
                if _is_transient_vision_error(exc):
                    break
                raise RuntimeError(_friendly_vision_error(exc)) from exc

    assert last_error is not None
    raise RuntimeError(_friendly_vision_error(last_error))


# ── LM Studio backend (OpenAI-uyumlu vision) ────────────────────────────────

def _analyze_with_lmstudio(query: str, image_path: Path, owner_name: str, window_title: str) -> str:
    base = str(get_app_config_value("lmstudio_base_url", "http://127.0.0.1:1234/v1") or "").rstrip("/")
    api_key = str(get_app_config_value("lmstudio_api_key", "lm-studio") or "lm-studio")
    vision_model = str(get_app_config_value("lmstudio_vision_model", "") or "").strip()
    if not vision_model:
        vision_model = str(get_app_config_value("lmstudio_model", "local-model") or "local-model")

    prompt = _vision_prompt(query, owner_name, window_title)
    img_bytes, mime = _prepare_image_bytes(image_path)
    b64 = base64.b64encode(img_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    payload = {
        "model": vision_model,
        "temperature": 0.2,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    }

    retry_delays = (0.9, 1.8, 3.0)
    last_error: Exception | None = None
    for attempt, delay in enumerate(retry_delays, start=1):
        try:
            resp = requests.post(
                f"{base}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                data=json.dumps(payload),
                timeout=180,
            )
            if not resp.ok:
                text = resp.text or ""
                lower = text.lower()
                if resp.status_code in (400, 404, 422) and (
                    "image" in lower or "vision" in lower or "multimodal" in lower or "unsupported" in lower
                ):
                    return (
                        "LM Studio'da yuklu model goruntu (vision) desteklemiyor gibi gorunuyor. "
                        "LM Studio'da bir vision modeli yukleyip 'lmstudio_vision_model' ayarini "
                        "(veya 'lmstudio_model' degerini) o modele ayarla. "
                        f"Sunucu yaniti: HTTP {resp.status_code} - {text[:200]}"
                    )
                raise RuntimeError(f"LM Studio {resp.status_code}: {text[:300]}")

            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("LM Studio bos cevap dondurdu.")
            msg = choices[0].get("message", {}) or {}
            content = msg.get("content")
            text_out = ""
            if isinstance(content, str):
                text_out = content.strip()
            elif isinstance(content, list):
                pieces: list[str] = []
                for part in content:
                    if isinstance(part, dict):
                        t = part.get("text") or part.get("content") or ""
                        if isinstance(t, str) and t.strip():
                            pieces.append(t.strip())
                text_out = "\n".join(pieces).strip()
            if text_out:
                return text_out
            raise RuntimeError("LM Studio gecerli bir ekran analizi metni dondurmedi.")
        except requests.exceptions.ConnectionError as exc:
            return (
                "LM Studio sunucusuna baglanilamadi. LM Studio acik mi ve sunucu "
                f"({base}) calisiyor mu? Hata: {exc}"
            )
        except Exception as exc:
            last_error = exc
            if attempt < len(retry_delays) and _is_transient_vision_error(exc):
                time.sleep(delay)
                continue
            raise RuntimeError(_friendly_vision_error(exc)) from exc

    assert last_error is not None
    raise RuntimeError(_friendly_vision_error(last_error))


# ── Public API ───────────────────────────────────────────────────────────────

def analyze_screen(query: str, target: str = "active_window") -> str:
    target = (target or "active_window").strip().lower()
    if target != "active_window":
        return "Screen Vision v1 yalnizca aktif pencere analizini destekliyor."

    ok, detail, payload = _capture_active_window()
    if not ok:
        return detail or _screen_permission_message()

    image_path = Path(payload["image_path"])
    owner_name = str(payload.get("owner_name", "") or "").strip()
    window_title = str(payload.get("window_title", "") or "").strip()

    try:
        if not image_path.exists():
            return "Ekran goruntusu dosyasi bulunamadi. Tekrar dene."
        if image_path.stat().st_size <= 0:
            return "Ekran goruntusu bos geldi. " + _screen_permission_message()
        if _image_looks_blank(image_path):
            return (
                "Ekran goruntusu siyah veya bos gorunuyor. Bu, korumali bir uygulama "
                "(orn. DRM iceren video oynaticilari) acikken olabilir. "
                + _screen_permission_message()
            )
        try:
            if is_local_backend():
                analysis = _analyze_with_lmstudio(query, image_path, owner_name, window_title)
            else:
                analysis = _analyze_with_gemini(query, image_path, owner_name, window_title)
        except Exception as exc:
            prefix = f"{owner_name} / {window_title}".strip(" /")
            if prefix:
                return f"Ekran goruntusu alindi ({prefix}) ama analiz tamamlanamadi: {exc}"
            return f"Ekran goruntusu alindi ama analiz tamamlanamadi: {exc}"

        if owner_name or window_title:
            title = " / ".join(part for part in (owner_name, window_title) if part).strip()
            if title:
                return f"[Aktif pencere: {title}]\n{analysis}"
        return analysis
    finally:
        try:
            if image_path.exists():
                image_path.unlink()
        except Exception:
            pass
