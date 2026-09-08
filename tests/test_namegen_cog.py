import unittest

from core.command_model import CommandPlatform
from core.namegen_format import (
    format_namegen_output,
    uses_plain_text_namegen_output,
)


class NameGenFormattingTests(unittest.TestCase):
    def test_single_name_uses_plain_text(self):
        result = format_namegen_output(
            ["Ibloll (m) [vedalken]"],
            1,
            plain_text=True,
        )

        self.assertEqual(
            result,
            "<Generated 1 Random Name(s)>-- Ibloll (m) [vedalken]",
        )

    def test_multiple_names_are_comma_separated(self):
        result = format_namegen_output(
            ["Ibloll (m) [vedalken]", "Mialee (f) [elf]"],
            2,
            plain_text=True,
        )

        self.assertEqual(
            result,
            "<Generated 2 Random Name(s)>-- "
            "Ibloll (m) [vedalken], Mialee (f) [elf]",
        )

    def test_livestream_platforms_use_plain_text(self):
        for platform in (
            CommandPlatform.TWITCH,
            CommandPlatform.YOUTUBE,
            CommandPlatform.KICK,
            CommandPlatform.FACEBOOK,
            CommandPlatform.TIKTOK,
        ):
            with self.subTest(platform=platform.value):
                self.assertTrue(uses_plain_text_namegen_output(platform))

    def test_discord_output_retains_markdown(self):
        self.assertFalse(uses_plain_text_namegen_output(CommandPlatform.DISCORD))
        result = format_namegen_output(["Ibloll (m) [vedalken]"], 1)

        self.assertEqual(
            result,
            "**Generated 1 Random Name(s):**\n```Ibloll (m) [vedalken]```",
        )


if __name__ == "__main__":
    unittest.main()
