"""
Run terminal commands — Linux Bash.
"""

import subprocess


BLOCKED = [
    "rm -rf /",
    "rm -rf /*",
    "dd if=",
    "mkfs",
    "fdisk",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
    "chmod 777 /",
    "chown -R",
    "> /dev/sda",
    "| shutdown",
    "sudo rm",
    "sudo dd",
    "sudo mkfs",
    "sudo fdisk",
]

_PREFIX_BLOCK = (
    "rm ", "dd ", "mkfs", "fdisk",
    "sudo rm", "sudo dd", "sudo mkfs",
)


def _open_path(path: str) -> str:
    """Open a file/path in the default application."""
    try:
        subprocess.Popen(["xdg-open", path])
        return f"Opened: {path}"
    except Exception as e:
        return f"Could not open: {e}"


def shell_run(command: str, timeout: int = 30) -> str:
    if not command:
        return "No command specified."

    cmd_lower = command.lower().strip()

    # Handle "clear" command
    if cmd_lower in ("clear", "cls"):
        subprocess.run(["clear"], shell=True)
        return ""

    # Handle "open" commands (open a file/directory)
    if cmd_lower.startswith("open "):
        path = command[5:].strip()
        return _open_path(path)

    if cmd_lower.startswith(_PREFIX_BLOCK):
        return (
            "Security: Commands that modify files or permissions are not executed directly. "
            "Try a safer, more specific command."
        )

    for blocked in BLOCKED:
        if blocked in cmd_lower:
            return f"Security: This command is blocked -> {blocked}"

    try:
        result = subprocess.run(
            ["/bin/bash", "-c", command],
            capture_output=True, text=True, timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()
        if not output:
            return "Command executed successfully (no output)."
        if len(output) > 800:
            output = output[:800] + "\n... (output truncated)"
        return output
    except subprocess.TimeoutExpired:
        return f"Command timed out ({timeout}s)."
    except Exception as e:
        return f"Error: {e}"