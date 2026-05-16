"""
Terminal komutu calistirma — Windows PowerShell.
"""

import subprocess


BLOCKED = [
    "format c:",
    "format /q",
    "del /f /s /q c:\\",
    "rd /s /q c:\\",
    "rmdir /s /q c:\\",
    "shutdown",
    "logoff",
    "diskpart",
    "cipher /w:",
    "fsutil file setzerodata",
    "reg delete hklm",
    "bcdedit",
]

# Tek basina yazildiginda iz birakan komutlar (gercekten silen / yetki degistiren)
_PREFIX_BLOCK = (
    "del ", "erase ", "rd ", "rmdir ", "format ",
    "takeown ", "icacls ", "attrib +s",
    "remove-item ", "rm ", "ri ",
)


def shell_run(command: str, timeout: int = 30) -> str:
    if not command:
        return "Komut belirtilmedi."

    cmd_lower = command.lower().strip()

    if cmd_lower.startswith(_PREFIX_BLOCK):
        return (
            "Guvenlik: Dosya veya yetki degistiren komutlar dogrudan calistirilmiyor. "
            "Daha guvenli ve dar kapsamli bir komut dene."
        )

    for blocked in BLOCKED:
        if blocked in cmd_lower:
            return f"Guvenlik: Bu komut engellendi -> {blocked}"

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()
        if not output:
            return "Komut basariyla calisti (cikti yok)."
        if len(output) > 800:
            output = output[:800] + "\n... (cikti kisaltildi)"
        return output
    except subprocess.TimeoutExpired:
        return f"Komut zaman asimina ugradi ({timeout}s)."
    except Exception as e:
        return f"Hata: {e}"
