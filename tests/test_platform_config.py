import ast
import types
import unittest
from pathlib import Path

from core.command_model import CommandPlatform
from core.platform_config import is_platform_available, is_platform_enabled


TWITCH_PATH = Path(__file__).resolve().parents[1] / "src/eyebot_twitch.py"


def load_twitch_main(*, enabled):
    tree = ast.parse(TWITCH_PATH.read_text(encoding="utf-8"))
    main = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    module = ast.Module(body=[main], type_ignores=[])
    ast.fix_missing_locations(module)
    logger = types.SimpleNamespace(messages=[])
    logger.info = logger.messages.append
    logger.error = logger.messages.append

    class FakeBot:
        constructed = 0
        runs = 0

        def __init__(self):
            type(self).constructed += 1

        def run(self):
            type(self).runs += 1

    namespace = {
        "TWITCH_ENABLED": enabled,
        "logger": logger,
        "Bot": FakeBot,
        "validate_twitch_config": lambda: (),
    }
    exec(compile(module, str(TWITCH_PATH), "exec"), namespace)
    return namespace["main"], logger, FakeBot


class PlatformConfigTests(unittest.TestCase):
    def test_platform_must_be_explicitly_enabled(self):
        self.assertTrue(
            is_platform_enabled(
                {"twitch": {"enabled": True}},
                CommandPlatform.TWITCH,
            )
        )
        self.assertFalse(
            is_platform_enabled(
                {"twitch": {"enabled": False}},
                CommandPlatform.TWITCH,
            )
        )

    def test_missing_or_non_boolean_values_use_safe_default(self):
        self.assertFalse(is_platform_enabled({}, "twitch"))
        self.assertFalse(
            is_platform_enabled({"twitch": {"enabled": "true"}}, "twitch")
        )
        self.assertFalse(
            is_platform_enabled({"twitch": None}, "twitch")
        )

    def test_default_can_preserve_legacy_behavior_when_requested(self):
        self.assertTrue(is_platform_enabled({}, "legacy", default=True))

    def test_available_is_host_gate_with_legacy_enabled_fallback(self):
        self.assertFalse(
            is_platform_available(
                {"instagram": {"available": False, "enabled": True}},
                "instagram",
            )
        )
        self.assertTrue(
            is_platform_available(
                {"instagram": {"enabled": True}},
                "instagram",
            )
        )

    def test_disabled_twitch_does_not_construct_or_run_bot(self):
        main, logger, bot = load_twitch_main(enabled=False)
        main()
        self.assertEqual(bot.constructed, 0)
        self.assertEqual(bot.runs, 0)
        self.assertIn("disabled", logger.messages[0])

    def test_enabled_twitch_constructs_and_runs_bot(self):
        main, _logger, bot = load_twitch_main(enabled=True)
        main()
        self.assertEqual(bot.constructed, 1)
        self.assertEqual(bot.runs, 1)

    def test_enabled_twitch_rejects_missing_connection_config(self):
        main, logger, bot = load_twitch_main(enabled=True)
        main.__globals__["validate_twitch_config"] = lambda: (
            "twitch.tmi_token",
            "twitch.channels",
        )
        self.assertEqual(main(), 2)
        self.assertEqual(bot.constructed, 0)
        self.assertIn("twitch.tmi_token", logger.messages[0])
