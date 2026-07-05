"""
System information — Linux version (psutil + nmcli).
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
        results.append(f"Time: {now.strftime('%H:%M:%S')}")

    if query in ("date", "tarih", "all"):
        now = datetime.datetime.now()
        results.append(f"Date: {now.strftime('%d %B %Y, %A')}")

    if query in ("network", "ag", "ağ", "wifi", "all"):
        results.append(_network())

    if not results:
        results.append(f"Unknown query: {query}. Use battery/cpu/ram/disk/time/date/network/all.")

    return "\n".join(r for r in results if r)


def _battery() -> str:
    if HAS_PSUTIL:
        bat = psutil.sensors_battery()
        if bat:
            status = "Charging" if bat.power_plugged else "On battery"
            return f"Battery: %{bat.percent:.0f} - {status}"
        return "Battery sensor not found (may be a desktop system)."
    return "Battery information unavailable."


def _cpu() -> str:
    if HAS_PSUTIL:
        usage = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        freq_str = f", {freq.current:.0f} MHz" if freq else ""
        return f"CPU: %{usage:.1f} usage - {count} cores{freq_str}"
    return "CPU information unavailable."


def _ram() -> str:
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        total = vm.total / (1024 ** 3)
        used = vm.used / (1024 ** 3)
        pct = vm.percent
        return f"RAM: {used:.1f}GB / {total:.1f}GB in use (%{pct:.0f})"
    return "RAM information unavailable."


def _disk() -> str:
    """Check disk usage on the root partition."""
    if HAS_PSUTIL:
        du = psutil.disk_usage("/")
        total = du.total / (1024 ** 3)
        used = du.used / (1024 ** 3)
        free = du.free / (1024 ** 3)
        return f"Disk (/): {used:.1f}GB used, {free:.1f}GB free (total {total:.1f}GB)"
    return "Disk information unavailable."


def _network() -> str:
    """Get WiFi/network info via nmcli, falling back to psutil."""
    # Try nmcli first (Ubuntu ships with NetworkManager)
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            text=True, timeout=5, stderr=subprocess.DEVNULL,
        )
        for line in out.splitlines():
            parts = line.split(":", 1)
            if len(parts) == 2:
                active, ssid = parts
                if active == "yes" and ssid:
                    return f"WiFi: {ssid} connected"
    except Exception:
        pass

    # Fallback to psutil for IP info
    if HAS_PSUTIL:
        try:
            addrs = psutil.net_if_addrs()
            for iface, entries in addrs.items():
                for entry in entries:
                    addr = getattr(entry, "address", "")
                    if (
                        addr
                        and ":" not in addr
                        and not addr.startswith("127.")
                        and not addr.startswith("169.254.")
                    ):
                        return f"Network: {iface} IP {addr}"
        except Exception:
            pass

    return "No network connection found."