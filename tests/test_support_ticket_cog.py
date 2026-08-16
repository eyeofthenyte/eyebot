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


class FakeInstructionChannel:
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append({"args": args, **kwargs})
        return SimpleNamespace(id=123, jump_url="https://discord.com/channels/42/100/123")


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
                {"ticket", "ticket-setup", "ticket-guide", "resolved", "cancel", "ticket-status", "ticket-list", "ticket-reopen"}
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
        description_label = modal.children[0]
        self.assertEqual(modal.description_input.max_length, 4000)
        self.assertIn("4,000", description_label.description)
        self.assertIn("current/limit", description_label.description)
        self.assertIn("maximum 4,000 characters", modal.description_input.placeholder)

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

    def test_ticket_embed_supports_configured_4000_character_description(self):
        ticket = SupportTicket(
            number="T-000001",
            guild_id="42",
            opener_id="7",
            description="x" * 4000,
            opened_at="2026-08-16T00:00:00+00:00",
        )

        embed = Support.ticket_embed(None, ticket)

        self.assertEqual(len(embed.description), 4000)
        self.assertLessEqual(len(embed.description), 4096)

    def test_content_limit_failure_has_specific_ephemeral_message(self):
        class ContentLimitError:
            code = 50035

            def __str__(self):
                return "Invalid Form Body In content: Must be 2000 or fewer in length."

        cog = SimpleNamespace(maximum_description_length=4000)

        message = Support.ticket_delivery_failure_message(
            cog,
            ContentLimitError(),
            "posting the ticket contents",
        )

        self.assertIn("2,000-character limit", message)
        self.assertIn("4,000-character limit", message)
        self.assertIn("Please retry", message)

    async def test_close_modal_requires_a_brief_note(self):
        cog = FakeCog()
        cog.maximum_close_note_length = 1000

        modal = TicketCloseModal(cog, "T-000001", "resolve")

        self.assertEqual(modal.note_input.min_length, 5)
        self.assertEqual(modal.note_input.max_length, 1000)
        self.assertTrue(modal.note_input.required)

    async def test_support_instructions_embed_has_side_by_side_guides(self):
        embed = Support.support_instructions_embed()

        self.assertEqual(embed.title, "EyeBot Support Ticket Guide")
        self.assertEqual(len(embed.fields), 2)
        self.assertEqual(
            [field.name for field in embed.fields],
            ["👤 User Instructions", "🛡️ Moderator Instructions"],
        )
        self.assertTrue(all(field.inline for field in embed.fields))
        self.assertTrue(all(len(field.value) <= 1024 for field in embed.fields))

    async def test_post_support_instructions_sends_the_embed(self):
        channel = FakeInstructionChannel()

        message = await Support.post_support_instructions(channel)

        self.assertEqual(message.id, 123)
        self.assertEqual(len(channel.sent), 1)
        self.assertIsInstance(channel.sent[0]["embed"], discord.Embed)
        self.assertEqual(channel.sent[0]["embed"].title, "EyeBot Support Ticket Guide")

    async def test_audit_messages_are_silent_and_disable_mentions(self):
        channel = FakeInstructionChannel()
        cog = SimpleNamespace(
            mod_channel=lambda _guild: channel,
            logger=SimpleNamespace(error=lambda *args, **kwargs: None),
            safe_error=lambda error: str(error),
        )

        await Support.audit(cog, SimpleNamespace(id=42), "alice updated a ticket")

        self.assertTrue(channel.sent[0]["silent"])
        self.assertFalse(channel.sent[0]["allowed_mentions"].users)

    def test_plain_username_uses_account_name_without_a_mention(self):
        member = SimpleNamespace(name="plain_user", display_name="Server Nickname")

        self.assertEqual(Support.plain_username(member), "plain\\_user")

    def test_ticket_permission_check_rejects_user_without_parent_visibility(self):
        bot_permissions = SimpleNamespace(
            view_channel=True,
            send_messages=True,
            create_private_threads=True,
            send_messages_in_threads=True,
            manage_threads=True,
            attach_files=True,
        )
        user_permissions = SimpleNamespace(
            view_channel=False,
            send_messages_in_threads=True,
        )
        bot_member = object()
        user = object()
        channel = SimpleNamespace(
            mention="#support_tickets",
            permissions_for=lambda member: (
                bot_permissions if member is bot_member else user_permissions
            ),
        )

        problem = Support.ticket_permission_problem(
            channel,
            SimpleNamespace(me=bot_member),
            user,
        )

        self.assertIn("cannot view", problem)
        self.assertIn("View Channel", problem)

    def test_ticket_permission_check_reports_missing_bot_thread_permission(self):
        bot_permissions = SimpleNamespace(
            view_channel=True,
            send_messages=True,
            create_private_threads=False,
            send_messages_in_threads=True,
            manage_threads=True,
            attach_files=True,
        )
        channel = SimpleNamespace(
            mention="#support_tickets",
            permissions_for=lambda _member: bot_permissions,
        )

        problem = Support.ticket_permission_problem(
            channel,
            SimpleNamespace(me=object()),
            object(),
        )

        self.assertIn("Create Private Threads", problem)


if __name__ == "__main__":
    unittest.main()
