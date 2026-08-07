"""Return success while the configured EyeBot process is running."""

import os
from pathlib import Path


def bot_process_is_running(
    expected_process: str | None = None,
    *,
    proc_root: Path = Path("/proc"),
) -> bool:
    expected = (
        expected_process
        or os.getenv("EYEBOT_PROCESS")
        or "src/eyebot.py"
    ).encode()
    for command_line in proc_root.glob("[0-9]*/cmdline"):
        try:
            command = command_line.read_bytes().replace(b"\0", b" ")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if expected in command:
            return True
    return False


def discord_bot_is_running() -> bool:
    """Backward-compatible Discord-specific healthcheck."""
    return bot_process_is_running("src/eyebot_discord.py")


if __name__ == "__main__":
    raise SystemExit(0 if bot_process_is_running() else 1)
