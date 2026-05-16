"""
actions/health.py — Windows sistem sagligi (vitals).

Eski iPhone HealthAutoExport JSON akisinin yerine bu Windows surumu
psutil + WMI uzerinden makinenin canli "saglik" gostergelerini doner:
CPU, RAM, disk, pil, sicaklik, ag, uptime, surec sayisi.

Public API korunur:
  - get_health_data(query: str) -> str
  - get_welcome_health_summary() -> str
"""

from __future__ import annotations

import time
import shutil
import platform
import datetime as _dt

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import wmi  # type: ignore
    _WMI = wmi.WMI(namespace="root\\OpenHardwareMonitor")
    HAS_OHM = True
except Exception:
    _WMI = None
    HAS_OHM = False


# ── Yardimcilar ──────────────────────────────────────────────────────────────

def _normalize_query(text: str) -> str:
    text = (text or "").strip().lower()
    return (
        text.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
            .replace("ş", "s").replace("ö", "o").replace("ç", "c")
    )


def _uptime_str() -> str:
    if not HAS_PSUTIL:
        return "—"
    secs = time.time() - psutil.boot_time()
    mins, _ = divmod(int(secs), 60)
    hrs, mins = divmod(mins, 60)
    days, hrs = divmod(hrs, 24)
    if days:
        return f"{days} gün {hrs} saat"
    if hrs:
        return f"{hrs} saat {mins} dk"
    return f"{mins} dk"


def _battery() -> dict:
    if not HAS_PSUTIL:
        return {}
    bat = psutil.sensors_battery()
    if not bat:
        return {}
    out = {"percent": float(bat.percent), "plugged": bool(bat.power_plugged)}
    if bat.secsleft and bat.secsleft > 0 and bat.secsleft != psutil.POWER_TIME_UNLIMITED:
        out["minutes_left"] = int(bat.secsleft / 60)
    return out


def _cpu() -> dict:
    if not HAS_PSUTIL:
        return {}
    pct = psutil.cpu_percent(interval=0.3)
    freq = psutil.cpu_freq()
    return {
        "percent": pct,
        "cores": psutil.cpu_count(logical=True) or 0,
        "freq_ghz": (freq.current / 1000.0) if freq and freq.current else None,
    }


def _ram() -> dict:
    if not HAS_PSUTIL:
        return {}
    m = psutil.virtual_memory()
    return {
        "percent": m.percent,
        "used_gb": m.used / (1024 ** 3),
        "total_gb": m.total / (1024 ** 3),
    }


def _disk() -> dict:
    try:
        u = shutil.disk_usage("C:\\")
    except Exception:
        return {}
    return {
        "percent": (u.used / u.total) * 100 if u.total else 0,
        "used_gb": u.used / (1024 ** 3),
        "total_gb": u.total / (1024 ** 3),
        "free_gb": u.free / (1024 ** 3),
    }


def _temps() -> dict:
    """OpenHardwareMonitor varsa CPU/GPU sicakliklarini doner."""
    out = {}
    if HAS_OHM and _WMI is not None:
        try:
            for sensor in _WMI.Sensor():
                if sensor.SensorType != "Temperature":
                    continue
                name = (sensor.Name or "").lower()
                if "cpu" in name and "cpu" not in out:
                    out["cpu_c"] = float(sensor.Value)
                elif ("gpu" in name) and "gpu" not in out:
                    out["gpu_c"] = float(sensor.Value)
        except Exception:
            pass

    if HAS_PSUTIL and not out:
        try:
            temps = psutil.sensors_temperatures()  # Windows: cogu zaman bos
        except Exception:
            temps = {}
        if temps:
            for label, entries in temps.items():
                for e in entries:
                    if e.current and "cpu_c" not in out and "cpu" in label.lower():
                        out["cpu_c"] = float(e.current)
                    if e.current and "gpu_c" not in out and "gpu" in label.lower():
                        out["gpu_c"] = float(e.current)
    return out


def _net() -> dict:
    if not HAS_PSUTIL:
        return {}
    try:
        c = psutil.net_io_counters()
    except Exception:
        return {}
    return {
        "sent_mb": c.bytes_sent / (1024 ** 2),
        "recv_mb": c.bytes_recv / (1024 ** 2),
    }


def _processes() -> int:
    if not HAS_PSUTIL:
        return 0
    try:
        return len(psutil.pids())
    except Exception:
        return 0


def _collect() -> dict:
    return {
        "uptime": _uptime_str(),
        "battery": _battery(),
        "cpu": _cpu(),
        "ram": _ram(),
        "disk": _disk(),
        "temps": _temps(),
        "net": _net(),
        "procs": _processes(),
        "host": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "ts": time.time(),
    }


def _age_str(ts: float) -> str:
    return "az önce" if (time.time() - ts) < 60 else f"{int((time.time()-ts)/60)} dk önce"


# ── Formatlayicilar ──────────────────────────────────────────────────────────

def _fmt_pct(v) -> str:
    return f"{v:.0f}%" if isinstance(v, (int, float)) else "—"


def _fmt_battery(b: dict) -> str:
    if not b:
        return "Pil: bu makinede algılanmadı (masaüstü olabilir)"
    parts = [f"Pil: {_fmt_pct(b.get('percent'))}"]
    parts.append("şarjda" if b.get("plugged") else "pilde")
    if "minutes_left" in b:
        m = b["minutes_left"]
        parts.append(f"~{m//60} sa {m%60} dk kaldı" if m >= 60 else f"~{m} dk kaldı")
    return ", ".join(parts)


def _fmt_cpu(c: dict) -> str:
    if not c:
        return "CPU: —"
    out = f"CPU: {_fmt_pct(c.get('percent'))} ({c.get('cores')} çekirdek"
    if c.get("freq_ghz"):
        out += f", {c['freq_ghz']:.1f} GHz"
    return out + ")"


def _fmt_ram(r: dict) -> str:
    if not r:
        return "RAM: —"
    return f"RAM: {_fmt_pct(r.get('percent'))} ({r['used_gb']:.1f} / {r['total_gb']:.1f} GB)"


def _fmt_disk(d: dict) -> str:
    if not d:
        return "Disk C:: —"
    return f"Disk C:: {_fmt_pct(d.get('percent'))} dolu, {d['free_gb']:.1f} GB boş"


def _fmt_temps(t: dict) -> str:
    if not t:
        return "Sıcaklık: sensör yok (OpenHardwareMonitor önerilir)"
    parts = []
    if "cpu_c" in t:
        parts.append(f"CPU {t['cpu_c']:.0f}°C")
    if "gpu_c" in t:
        parts.append(f"GPU {t['gpu_c']:.0f}°C")
    return "Sıcaklık: " + ", ".join(parts) if parts else "Sıcaklık: —"


def _fmt_net(n: dict) -> str:
    if not n:
        return "Ağ: —"
    return f"Ağ trafiği: ↑{n['sent_mb']:.0f} MB  ↓{n['recv_mb']:.0f} MB"


# ── Ana fonksiyonlar ─────────────────────────────────────────────────────────

def get_health_data(query: str = "all") -> str:
    """
    Sistem sagligini Turkce ozet olarak doner.

    Sorgu anahtar kelimeleri:
      - "pil" / "battery"        → sadece pil
      - "cpu" / "islemci"        → sadece CPU
      - "ram" / "bellek"         → sadece RAM
      - "disk"                   → sadece disk
      - "sicaklik" / "isi"       → sadece sicaklik
      - "ag" / "network"         → sadece ag
      - "uptime" / "calisma"     → sadece uptime
      - "analiz" / "detay"       → detayli analiz
      - varsayilan / "all"       → tum vitals kart formatinda
    """
    if not HAS_PSUTIL:
        return "Sistem sağlığı okunamadı: psutil kurulu değil. `pip install psutil` ile kur."

    q = _normalize_query(query)
    data = _collect()
    age = _age_str(data["ts"])

    if any(k in q for k in ("pil", "battery", "sarj", "sarjda")):
        return f"{_fmt_battery(data['battery'])}\n[güncelleme: {age}]"

    if any(k in q for k in ("cpu", "islemci", "yuk", "load")):
        return f"{_fmt_cpu(data['cpu'])}\n[güncelleme: {age}]"

    if any(k in q for k in ("ram", "bellek", "memory")):
        return f"{_fmt_ram(data['ram'])}\n[güncelleme: {age}]"

    if any(k in q for k in ("disk", "depolama", "storage")):
        return f"{_fmt_disk(data['disk'])}\n[güncelleme: {age}]"

    if any(k in q for k in ("sicaklik", "isi", "temp", "fan", "soguma")):
        return f"{_fmt_temps(data['temps'])}\n[güncelleme: {age}]"

    if any(k in q for k in ("ag", "network", "internet", "wifi", "trafik")):
        return f"{_fmt_net(data['net'])}\n[güncelleme: {age}]"

    if any(k in q for k in ("uptime", "calisma suresi", "calisma", "acik kalma")):
        return f"Sistem {data['uptime']} açık.\n[güncelleme: {age}]"

    if any(k in q for k in ("analiz", "detay", "rapor", "ozet detayli")):
        return _build_analysis(data, age)

    # Varsayilan: kart formatinda tam vitals
    return "\n".join([
        "── SİSTEM SAĞLIĞI ─────────────────",
        f"🖥  {data['host']} — {data['os']}",
        f"⏱  Uptime        : {data['uptime']}",
        f"🔋 {_fmt_battery(data['battery'])}",
        f"⚙  {_fmt_cpu(data['cpu'])}",
        f"🧠 {_fmt_ram(data['ram'])}",
        f"💾 {_fmt_disk(data['disk'])}",
        f"🌡  {_fmt_temps(data['temps'])}",
        f"🌐 {_fmt_net(data['net'])}",
        f"🧩 Süreç sayısı   : {data['procs']}",
        "──────────────────────────────────",
        f"[güncelleme: {age}]",
    ])


def _build_analysis(data: dict, age: str) -> str:
    cpu = data["cpu"].get("percent") or 0
    ram = data["ram"].get("percent") or 0
    disk = data["disk"].get("percent") or 0
    bat = data["battery"]

    lines = ["Sistem analizi hazır."]

    if cpu >= 85:
        lines.append(f"CPU yükü yüksek (%{cpu:.0f}) — arka planda ağır iş var.")
    elif cpu >= 50:
        lines.append(f"CPU orta yükte (%{cpu:.0f}).")
    else:
        lines.append(f"CPU rahat (%{cpu:.0f}).")

    if ram >= 85:
        lines.append(f"RAM dolmak üzere (%{ram:.0f}) — gereksiz uygulamaları kapatmak iyi olur.")
    elif ram >= 65:
        lines.append(f"RAM orta seviyede (%{ram:.0f}).")
    else:
        lines.append(f"RAM bol (%{ram:.0f}).")

    if disk >= 90:
        lines.append(f"Disk C: kritik dolulukta (%{disk:.0f}).")
    elif disk >= 75:
        lines.append(f"Disk C: %{disk:.0f} dolu — temizlik mantıklı.")

    if bat:
        if not bat.get("plugged") and bat.get("percent", 100) <= 20:
            lines.append("Pil düşük ve şarjda değil — şarja takmanı öneririm.")
        elif bat.get("plugged"):
            lines.append(f"Pil şarjda (%{bat.get('percent', 0):.0f}).")

    temps = data["temps"]
    if temps.get("cpu_c", 0) >= 85:
        lines.append(f"CPU sıcak: {temps['cpu_c']:.0f}°C — havalandırmayı kontrol et.")
    if temps.get("gpu_c", 0) >= 85:
        lines.append(f"GPU sıcak: {temps['gpu_c']:.0f}°C.")

    lines.append(f"Uptime: {data['uptime']}, süreç sayısı: {data['procs']}.")
    lines.append(f"[güncelleme: {age}]")
    return "\n".join(lines)


def get_health_card_lines() -> list[str]:
    """UI sol panelindeki dar HEALTH karti icin kisa, tek-satirlik vitals."""
    if not HAS_PSUTIL:
        return ["psutil yok"]
    data = _collect()
    lines: list[str] = []

    cpu = data["cpu"].get("percent")
    if cpu is not None:
        lines.append(f"CPU %{cpu:.0f}")

    ram = data["ram"]
    if ram:
        lines.append(f"RAM %{ram.get('percent', 0):.0f} ({ram.get('used_gb', 0):.1f}G)")

    disk = data["disk"]
    if disk:
        lines.append(f"Disk %{disk.get('percent', 0):.0f}, {disk.get('free_gb', 0):.0f}G boş")

    bat = data["battery"]
    if bat:
        tag = "şarjda" if bat.get("plugged") else "pilde"
        lines.append(f"Pil %{bat.get('percent', 0):.0f} {tag}")

    temps = data["temps"]
    if temps.get("cpu_c"):
        t = f"CPU {temps['cpu_c']:.0f}°C"
        if temps.get("gpu_c"):
            t += f" / GPU {temps['gpu_c']:.0f}°C"
        lines.append(t)
    elif data["uptime"] != "—":
        lines.append(f"Uptime {data['uptime']}")

    return lines[:5] or ["Veri yok"]


def get_welcome_health_summary() -> str:
    """Acilis ekraninda okunan kisa, dogal Turkce ozet."""
    if not HAS_PSUTIL:
        return "Sistem sağlığı şu anda alınamadı."

    data = _collect()
    parts = []

    bat = data["battery"]
    if bat:
        state = "şarjda" if bat.get("plugged") else "pilde"
        parts.append(f"pil {state} %{bat.get('percent', 0):.0f}")

    cpu_pct = data["cpu"].get("percent")
    if cpu_pct is not None:
        parts.append(f"CPU %{cpu_pct:.0f}")

    ram_pct = data["ram"].get("percent")
    if ram_pct is not None:
        parts.append(f"RAM %{ram_pct:.0f}")

    if data["uptime"] != "—":
        parts.append(f"sistem {data['uptime']} açık")

    if not parts:
        return "Sistem sağlığı şu anda alınamadı."

    if len(parts) == 1:
        return parts[0].capitalize() + "."
    return ", ".join(parts[:-1]).capitalize() + f" ve {parts[-1]}."
