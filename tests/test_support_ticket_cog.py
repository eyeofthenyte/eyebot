import unittest
import tempfile
from types import SimpleNamespace

import discord
from discord.ext import commands

from cogs.support import (
    Support,
    TicketCloseModal,
    TicketControlView,
    TicketModal,
    download_ticket_images,
)
from services.supportTicketService import SupportTicket


class FakeService:
    maximum_images = 4
    settings = {"max_image_bytes": 1024}

    def validate_images(self, images):
        return tuple(images)

    def sanitize_image(self, image):
        return image


class FakeCog:
    maximum_description_length = 4000
    service = FakeService()


class FakeAttachment:
    filename = "proof.png"
    content_type = "image/png"
    data = b"image-data"
    size = len(data)

    def __init__(self):
        self.read_count = 0

    async def read(self, *, use_cached=False):
        self.read_count += 1
        return self.data


class SupportTicketCogTests(unittest.IsolatedAsyncioTestCase):
    async def test_support_application_commands_register_with_bot_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
            bot.logger = SimpleNamespace(
                info=lambda *args, **kwargs: None,
                error=lambda *args, **kwargs: None,
            )
            bot.config = {"prefix": "!", "support_tickets": {}}
            bot.platform_config_service = SimpleNamespace(
                guild_config_dir=directory
            )

            await bot.add_cog(Support(bot))

            names = {command.name for command in bot.tree.get_commands()}
            self.assertTrue(
                {"ticket", "ticket-setup", "resolved", "cancel", "ticket-status", "ticket-list", "ticket-reopen"}
                <= names
            )
            await bot.close()

    async def test_ticket_modal_uses_labels_and_four_optional_images(self):
        modal = TicketModal(FakeCog(), 42, 7)

        self.assertEqual(len(modal.children), 3)
        self.assertTrue(all(isinstance(item, discord.ui.Label) for item in modal.children))
        self.assertIsInstance(modal.images_input, discord.ui.FileUpload)
        self.assertFalse(modal.images_input.required)
        self.assertEqual(modal.images_input.min_values, 0)
        self.assertEqual(modal.images_input.max_values, 4)

    async def test_modal_images_are_downloaded_immediately(self):
        attachment = FakeAttachment()

        images = await download_ticket_images(FakeService(), (attachment,))

        self.assertEqual(attachment.read_count, 1)
        self.assertEqual(images[0].filename, "proof.png")

    async def test_ticket_controls_disable_after_final_state(self):
        open_ticket = SupportTicket(
            number="T-000001",
            guild_id="42",
            opener_id="7",
            description="A sufficiently long ticket description.",
            opened_at="2026-08-15T00:00:00+00:00",
        )
        closed_ticket = SupportTicket.from_dict(
            {**open_ticket.to_dict(), "status": "resolved"}
        )

        open_view = TicketControlView(FakeCog(), open_ticket)
        closed_view = TicketControlView(FakeCog(), closed_ticket)

        self.assertFalse(open_view.children[0].disabled)
        self.assertTrue(all(item.disabled for item in closed_view.children))

    async def test_close_modal_requires_a_brief_note(self):
        cog = FakeCog()
        cog.maximum_close_note_length = 1000

        modal = TicketCloseModal(cog, "T-000001", "resolve")

        self.assertEqual(modal.note_input.min_length, 5)
        self.assertEqual(modal.note_input.max_length, 1000)
        self.assertTrue(modal.note_input.required)


if __name__ == "__main__":
    unittest.main()
