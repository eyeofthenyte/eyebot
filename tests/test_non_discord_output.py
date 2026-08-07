import unittest

from core.transport import strip_non_discord_attachment_suffix


class NonDiscordOutputTests(unittest.TestCase):
    def test_removes_attachment_marker_and_everything_after_it(self):
        self.assertEqual(
            strip_non_discord_attachment_suffix(
                "Result text | Attachments: image.png | hidden metadata"
            ),
            "Result text",
        )

    def test_preserves_output_without_attachment_marker(self):
        self.assertEqual(
            strip_non_discord_attachment_suffix("Result text | Total: 17"),
            "Result text | Total: 17",
        )
