"""
Sistem bilgisi — Windows surumu (psutil + netsh wlan).
"""

import subprocess
import datetime
import os

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def sys_info(query: str) -> str:
    query = query.lower().strip()

    results = []

    if query in ("battery", "pil", "all"):
        results.append(_battery())

    if query in ("cpu", "islemci", "işlemci", "all"):
        results.append(_cpu())

    if query in ("ram", "bellek", "memory", "all"):
        results.append(_ram())

    if query in ("disk", "depolama", "all"):
        results.append(_disk())

    if query in ("time", "saat", "zaman", "all"):
        now = datetime.datetime.now()
        results.append(f"Saat: {now.strftime('%H:%M:%S')}")

    if query in ("date", "tarih", "all"):
        now = datetime.datetime.now()
        results.append(f"Tarih: {now.strftime('%d %B %Y, %A')}")

    if query in ("network", "ag", "ağ", "wifi", "all"):
        results.append(_network())

    if not results:
        results.append(f"Bilinmeyen sorgu: {query}. battery/cpu/ram/disk/time/date/network/all kullanin.")

    return "\n".join(r for r in results if r)


def _battery() -> str:
    if HAS_PSUTIL:
        bat = psutil.sensors_battery()
        if bat:
            status = "Sarj oluyor" if bat.power_plugged else "Pilde"
            return f"Pil: %{bat.percent:.0f} - {status}"
        return "Pil sensoru bulunamadi (masaustu sistem olabilir)."
    return "Pil bilgisi alinamadi."


def _cpu() -> str:
    if HAS_PSUTIL:
        usage = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        freq_str = f", {freq.current:.0f} MHz" if freq else ""
        return f"CPU: %{usage:.1f} kullanim - {count} cekirdek{freq_str}"
    return "CPU bilgisi alinamadi."


def _ram() -> str:
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        total = vm.total / (1024 ** 3)
        used = vm.used / (1024 ** 3)
        pct = vm.percent
        return f"RAM: {used:.1f}GB / {total:.1f}GB kullanimda (%{pct:.0f})"
    return "RAM bilgisi alinamadi."


def _disk() -> str:
    drive = os.environ.get("SystemDrive", "C:") + "\\"
    if HAS_PSUTIL:
        du = psutil.disk_usage(drive)
        total = du.total / (1024 ** 3)
        used = du.used / (1024 ** 3)
        free = du.free / (1024 ** 3)
        return f"Disk ({drive}): {used:.1f}GB kullanildi, {free:.1f}GB bos (toplam {total:.1f}GB)"
    return "Disk bilgisi alinamadi."


def _network() -> str:
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True, timeout=5, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="ignore",
        )
        ssid = None
        state = None
        for line in out.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("ssid") and "bssid" not in stripped.lower():
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    ssid = parts[1].strip()
            if stripped.lower().startswith(("state", "durum")):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    state = parts[1].strip()
        if ssid:
            return f"WiFi: {ssid} bagli"
        if state:
            return f"WiFi durumu: {state}"
    except Exception:
        pass

    if HAS_PSUTIL:
        try:
            addrs = psutil.net_if_addrs()
            for iface, entries in addrs.items():
                for entry in entries:
                    addr = getattr(entry, "address", "")
                    family = getattr(entry, "family", None)
                    if (
                        addr
                        and ":" not in addr
                        and not addr.startswith("127.")
                        and not addr.startswith("169.254.")
                        and getattr(family, "name", str(family)).endswith("AF_INET")
                    ):
                        return f"Ag: {iface} IP {addr}"
        except Exception:
            pass

    return "Ag baglantisi bulunamadi."
