"""Start and supervise every enabled EyeBot platform process."""

from __future__ import annotations

import logging
import json
import os
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from core.platform_config import is_platform_enabled
from services.platformConfigService import load_split_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.getenv("EYEBOT_CONFIG_PATH", PROJECT_ROOT / "config.yaml"))
PLATFORM_CONFIG_PATH = Path(
    os.getenv("EYEBOT_PLATFORM_CONFIG_PATH", PROJECT_ROOT / "platforms.yaml")
)
CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = int(os.getenv("EYEBOT_CONTROL_PORT", "8765"))

PLATFORM_ENTRYPOINTS = {
    "discord": "src/eyebot_discord.py",
    "twitch": "src/eyebot_twitch.py",
    "youtube": "src/eyebot_youtube.py",
    "facebook": "src/eyebot_facebook.py",
    "kick": "src/eyebot_kick.py",
    "twitter": "src/eyebot_twitter.py",
    "bluesky": "src/eyebot_bluesky.py",
    "tiktok": "src/eyebot_tiktok.py",
    "instagram": "src/eyebot_instagram.py",
    "substack": "src/eyebot_substack.py",
    "kofi": "src/eyebot_kofi.py",
}

logger = logging.getLogger("eyebot.supervisor")


def load_supervisor_config(
    config_path: Path = CONFIG_PATH,
    platform_config_path: Path | None = None,
) -> Mapping:
    """Load a real, non-empty configuration file for supervised startup."""
    if not config_path.is_file():
        raise FileNotFoundError(
            f"EyeBot configuration file not found: {config_path}. "
            "Mount a host config.yaml at /app/config.yaml."
        )
    if platform_config_path is None:
        platform_config_path = (
            PLATFORM_CONFIG_PATH
            if config_path == CONFIG_PATH
            else config_path.with_name("platforms.yaml")
        )
    config, global_service, _platform_service = load_split_config(
        config_path,
        platform_config_path,
        guild_config_dir=os.getenv(
            "EYEBOT_GUILD_CONFIG_DIR",
            str(config_path.resolve().parent / "data" / "guilds"),
        ),
    )
    global_config = global_service.get()
    if not isinstance(global_config, Mapping) or not global_config:
        raise ValueError(
            f"EyeBot configuration is empty or invalid: {config_path}"
        )
    return config


def enabled_platforms(config: Mapping) -> tuple[str, ...]:
    """Return enabled platforms in deterministic startup order."""
    return tuple(
        platform
        for platform in PLATFORM_ENTRYPOINTS
        if is_platform_enabled(
            config,
            platform,
            default=platform == "discord",
        )
    )


class BotSupervisor:
    """Own platform subprocesses and shut them down as a group."""

    def __init__(self, platforms: Sequence[str]):
        self.platforms = tuple(platforms)
        self.processes: dict[str, subprocess.Popen] = {}
        self.stopping = False
        self._lock = threading.RLock()

    def _spawn(self, platform: str) -> subprocess.Popen:
        command = [sys.executable, PLATFORM_ENTRYPOINTS[platform]]
        logger.info("Starting %s bot: %s", platform, " ".join(command))
        return subprocess.Popen(command, cwd=PROJECT_ROOT)

    @staticmethod
    def _stop_process(platform: str, process: subprocess.Popen) -> None:
        if process.poll() is None:
            logger.info("Stopping %s bot", platform)
            process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            logger.warning("%s bot did not stop gracefully; killing it", platform)
            process.kill()
            process.wait()

    def start(self) -> None:
        with self._lock:
            for platform in self.platforms:
                self.processes[platform] = self._spawn(platform)

    def restart(self, platform: str) -> str:
        platform = platform.strip().lower()
        with self._lock:
            if platform not in PLATFORM_ENTRYPOINTS:
                raise ValueError(f"Unknown platform: {platform}")
            if platform not in self.processes:
                raise ValueError(f"{platform} is not enabled or running")
            if self.stopping:
                raise RuntimeError("EyeBot is shutting down")

            old_process = self.processes[platform]
            logger.info("Restarting %s bot", platform)
            self._stop_process(platform, old_process)
            self.processes[platform] = self._spawn(platform)
            return f"{platform} restarted"

    def stop(self) -> None:
        with self._lock:
            if self.stopping:
                return
            self.stopping = True
            for platform, process in self.processes.items():
                self._stop_process(platform, process)

    def wait(self) -> int:
        while not self.stopping:
            with self._lock:
                for platform, process in self.processes.items():
                    return_code = process.poll()
                    if return_code is not None:
                        logger.error(
                            "%s bot exited unexpectedly with status %s",
                            platform,
                            return_code,
                        )
                        self.stop()
                        return return_code or 1
            time.sleep(0.5)
        return 0


def send_restart_command(
    platform: str,
    *,
    host: str = CONTROL_HOST,
    port: int = CONTROL_PORT,
    timeout: float = 10,
) -> str:
    """Ask the running supervisor to restart one enabled platform."""
    request = json.dumps(
        {"command": "restart", "platform": platform.strip().lower()}
    ).encode() + b"\n"
    with socket.create_connection((host, port), timeout=timeout) as client:
        client.sendall(request)
        response_bytes = client.makefile("rb").readline()
    if not response_bytes:
        raise RuntimeError("The EyeBot supervisor returned no response")
    response = json.loads(response_bytes)
    if not response.get("ok"):
        raise RuntimeError(str(response.get("error", "Restart failed")))
    return str(response["message"])


class _ControlHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            request_bytes = self.rfile.readline(4097)
            if len(request_bytes) > 4096:
                raise ValueError("Supervisor command is too long")
            request = json.loads(request_bytes)
            if request.get("command") != "restart":
                raise ValueError("Unsupported supervisor command")
            message = self.server.supervisor.restart(
                str(request.get("platform", ""))
            )
            response = {"ok": True, "message": message}
        except (json.JSONDecodeError, TypeError, ValueError, RuntimeError) as error:
            response = {"ok": False, "error": str(error)}
        self.wfile.write(json.dumps(response).encode() + b"\n")


class SupervisorControlServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(
        self,
        supervisor: BotSupervisor,
        *,
        host: str = CONTROL_HOST,
        port: int = CONTROL_PORT,
    ):
        self.supervisor = supervisor
        super().__init__((host, port), _ControlHandler)


def _run_supervisor() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    try:
        config = load_supervisor_config()
    except (OSError, ValueError) as error:
        logger.error("%s", error)
        return 2
    logger.info("Loaded configuration from %s", CONFIG_PATH)
    platforms = enabled_platforms(config)
    if not platforms:
        logger.error(
            "No platform bots are enabled. Set at least one "
            "<platform>.enabled value to true in platforms.yaml."
        )
        return 2

    supervisor = BotSupervisor(platforms)

    def request_shutdown(signum, _frame):
        logger.info("Received signal %s", signum)
        supervisor.stop()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    try:
        supervisor.start()
        with SupervisorControlServer(supervisor) as server:
            control_thread = threading.Thread(
                target=server.serve_forever,
                name="eyebot-control",
                daemon=True,
            )
            control_thread.start()
            try:
                return supervisor.wait()
            finally:
                server.shutdown()
                control_thread.join(timeout=5)
    finally:
        supervisor.stop()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments:
        if len(arguments) != 2 or arguments[0].lower() != "restart":
            print(
                "Usage: python src/eyebot.py [restart <platform>]",
                file=sys.stderr,
            )
            return 2
        try:
            print(send_restart_command(arguments[1]))
            return 0
        except (OSError, RuntimeError, json.JSONDecodeError) as error:
            print(f"Restart failed: {error}", file=sys.stderr)
            return 1
    return _run_supervisor()


if __name__ == "__main__":
    raise SystemExit(main())
