import tempfile
import unittest
from pathlib import Path

from healthcheck import bot_process_is_running


class HealthcheckTests(unittest.TestCase):
    def test_finds_configured_bot_process(self):
        with tempfile.TemporaryDirectory() as directory:
            proc_root = Path(directory)
            process = proc_root / "10"
            process.mkdir()
            (process / "cmdline").write_bytes(
                b"python\0src/eyebot_twitch.py\0"
            )
            self.assertTrue(
                bot_process_is_running(
                    "src/eyebot_twitch.py",
                    proc_root=proc_root,
                )
            )
            self.assertFalse(
                bot_process_is_running(
                    "src/eyebot_discord.py",
                    proc_root=proc_root,
                )
            )
