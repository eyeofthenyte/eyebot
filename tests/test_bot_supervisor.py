import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from eyebot import (
    BotSupervisor,
    SupervisorControlServer,
    enabled_platforms,
    load_supervisor_config,
    send_restart_command,
)


class FakeProcess:
    def __init__(self, return_code=None):
        self.return_code = return_code
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.return_code

    def terminate(self):
        self.terminated = True
        self.return_code = 0

    def kill(self):
        self.killed = True
        self.return_code = -9

    def wait(self, timeout=None):
        return self.return_code


class EnabledPlatformTests(unittest.TestCase):
    def test_discord_defaults_to_enabled_for_legacy_configuration(self):
        self.assertEqual(enabled_platforms({}), ("discord",))

    def test_only_explicitly_enabled_optional_platforms_are_returned(self):
        config = {
            "discord": {"enabled": False},
            "twitch": {"enabled": True},
            "youtube": {"enabled": True},
            "kick": {"enabled": "true"},
        }
        self.assertEqual(enabled_platforms(config), ("twitch", "youtube"))

    def test_available_platform_starts_for_enabled_guild(self):
        config = {
            "discord": {"available": True, "enabled": True},
            "instagram": {"available": True, "enabled": False},
            "tiktok": {"available": False, "enabled": False},
        }
        guilds = {
            "42": {
                "platforms": {
                    "instagram": {"enabled": True},
                    "tiktok": {"enabled": True},
                }
            }
        }
        self.assertEqual(enabled_platforms(config, guilds), ("discord", "instagram"))

    def test_supervisor_requires_a_real_nonempty_config_file(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            with self.assertRaises(FileNotFoundError):
                load_supervisor_config(config_path)

            config_path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty or invalid"):
                load_supervisor_config(config_path)

    def test_supervisor_loads_selected_config_file(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text(
                "discord:\n  enabled: false\n"
                "twitch:\n  enabled: true\n",
                encoding="utf-8",
            )

            config = load_supervisor_config(config_path)

        self.assertTrue(config["twitch"]["enabled"])


class BotSupervisorTests(unittest.TestCase):
    @patch("eyebot.subprocess.Popen")
    def test_starts_one_child_for_each_enabled_platform(self, popen):
        popen.side_effect = [FakeProcess(), FakeProcess()]
        supervisor = BotSupervisor(("discord", "twitch"))

        supervisor.start()

        self.assertEqual(popen.call_count, 2)
        self.assertEqual(
            popen.call_args_list[0].args[0][-1],
            "src/eyebot_discord.py",
        )
        self.assertEqual(
            popen.call_args_list[1].args[0][-1],
            "src/eyebot_twitch.py",
        )

    def test_child_failure_stops_sibling_and_returns_failure(self):
        failed = FakeProcess(return_code=3)
        sibling = FakeProcess()
        supervisor = BotSupervisor(("discord", "twitch"))
        supervisor.processes = {"discord": failed, "twitch": sibling}

        self.assertEqual(supervisor.wait(), 3)
        self.assertTrue(sibling.terminated)

    def test_successful_unexpected_exit_is_still_container_failure(self):
        supervisor = BotSupervisor(("discord",))
        supervisor.processes = {"discord": FakeProcess(return_code=0)}

        self.assertEqual(supervisor.wait(), 1)

    @patch("eyebot.subprocess.Popen")
    def test_restarts_only_an_enabled_running_platform(self, popen):
        replacement = FakeProcess()
        popen.return_value = replacement
        original = FakeProcess()
        supervisor = BotSupervisor(("discord",))
        supervisor.processes = {"discord": original}

        self.assertEqual(supervisor.restart("DISCORD"), "discord restarted")
        self.assertTrue(original.terminated)
        self.assertIs(supervisor.processes["discord"], replacement)

        with self.assertRaisesRegex(ValueError, "not enabled or running"):
            supervisor.restart("twitch")
        with self.assertRaisesRegex(ValueError, "Unknown platform"):
            supervisor.restart("not-a-platform")

    @patch("eyebot.subprocess.Popen")
    def test_reconcile_starts_and_stops_workers(self, popen):
        popen.return_value = FakeProcess()
        discord = FakeProcess()
        twitch = FakeProcess()
        supervisor = BotSupervisor(("discord", "twitch"))
        supervisor.processes = {"discord": discord, "twitch": twitch}

        message = supervisor.reconcile(("discord", "instagram"))

        self.assertTrue(twitch.terminated)
        self.assertIn("instagram", supervisor.processes)
        self.assertIn("instagram", message)


class SupervisorControlTests(unittest.TestCase):
    @patch("eyebot.subprocess.Popen")
    def test_shell_client_restarts_platform_through_control_socket(self, popen):
        popen.return_value = FakeProcess()
        supervisor = BotSupervisor(("twitch",))
        supervisor.processes = {"twitch": FakeProcess()}
        with SupervisorControlServer(supervisor, port=0) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                result = send_restart_command(
                    "twitch",
                    port=server.server_address[1],
                )
            finally:
                server.shutdown()
                thread.join()

        self.assertEqual(result, "twitch restarted")

    def test_shell_client_reports_disabled_platform(self):
        supervisor = BotSupervisor(("discord",))
        supervisor.processes = {"discord": FakeProcess()}
        with SupervisorControlServer(supervisor, port=0) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "not enabled or running",
                ):
                    send_restart_command(
                        "twitch",
                        port=server.server_address[1],
                    )
            finally:
                server.shutdown()
                thread.join()
