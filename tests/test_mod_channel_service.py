import unittest
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock


class FakeAllowedMentions:
    def __init__(self):
        self.users = False
        self.roles = False
        self.everyone = False

    @classmethod
    def none(cls):
        return cls()


class FakeEmbed:
    def __init__(self, title=None, description=None, **_kwargs):
        self.title = title
        self.description = description
        self.fields = []

    def add_field(self, *, name, value, inline=True):
        self.fields.append(SimpleNamespace(name=name, value=value, inline=inline))

    def to_dict(self):
        result = {"type": "rich"}
        if self.title is not None:
            result["title"] = self.title
        if self.description is not None:
            result["description"] = self.description
        if self.fields:
            result["fields"] = [vars(field) for field in self.fields]
        return result

    @classmethod
    def from_dict(cls, value):
        embed = cls(value.get("title"), value.get("description"))
        for field in value.get("fields", []):
            embed.add_field(**field)
        return embed


discord = types.ModuleType("discord")
discord.AllowedMentions = FakeAllowedMentions
discord.Embed = FakeEmbed
sys.modules.setdefault("discord", discord)

from services.modChannelService import ModChannelHandler


class FakeGuild:
    id = 42

    def __init__(self, members=None, channels=None):
        self.members = members or {}
        self.channels = channels or {}

    def get_member(self, member_id):
        return self.members.get(member_id)

    def get_channel(self, channel_id):
        return self.channels.get(channel_id)


class ModChannelHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.channel = SimpleNamespace(send=AsyncMock())
        self.member = SimpleNamespace(id=123, name="plain_username")
        self.guild = FakeGuild(
            members={123: self.member}, channels={456: self.channel}
        )
        config_service = SimpleNamespace(
            discord_guilds=lambda: {"42": {"mod_channel": "456"}}
        )
        self.bot = SimpleNamespace(
            platform_config_service=config_service,
            get_user=lambda _user_id: None,
        )
        self.handler = ModChannelHandler(self.bot)

    def test_sanitize_text_replaces_both_user_mention_forms(self):
        result = self.handler.sanitize_text(
            self.guild, "<@123> changed a setting for <@!123>."
        )
        self.assertEqual(
            result, "plain_username changed a setting for plain_username."
        )

    def test_unknown_user_mention_is_still_plain_text(self):
        self.assertEqual(
            self.handler.sanitize_text(self.guild, "Changed by <@999>"),
            "Changed by user-999",
        )

    async def test_send_uses_configured_channel_and_disables_mentions(self):
        await self.handler.send(self.guild, content="Changed by <@123>")

        kwargs = self.channel.send.await_args.kwargs
        self.assertEqual(kwargs["content"], "Changed by plain_username")
        self.assertIsInstance(kwargs["allowed_mentions"], FakeAllowedMentions)
        self.assertFalse(kwargs["allowed_mentions"].users)
        self.assertFalse(kwargs["allowed_mentions"].roles)
        self.assertFalse(kwargs["allowed_mentions"].everyone)

    async def test_send_sanitizes_embed_text(self):
        embed = discord.Embed(
            title="Audit for <@123>", description="Changed by <@!123>"
        )
        embed.add_field(name="Actor <@123>", value="<@123>")

        await self.handler.send(self.guild, embed=embed)

        sent = self.channel.send.await_args.kwargs["embed"]
        self.assertEqual(sent.title, "Audit for plain_username")
        self.assertEqual(sent.description, "Changed by plain_username")
        self.assertEqual(sent.fields[0].name, "Actor plain_username")
        self.assertEqual(sent.fields[0].value, "plain_username")

    async def test_send_sanitizes_multiple_embeds(self):
        embeds = [
            discord.Embed(title="Before <@123>", description="<@123>"),
            discord.Embed(title="After <@!123>", description="<@!123>"),
        ]

        await self.handler.send(self.guild, embeds=embeds)

        sent = self.channel.send.await_args.kwargs["embeds"]
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0].title, "Before plain_username")
        self.assertEqual(sent[1].description, "plain_username")

    async def test_missing_mod_channel_skips_send(self):
        self.bot.platform_config_service.discord_guilds = lambda: {
            "42": {"mod_channel": "UNSET"}
        }
        self.assertIsNone(await self.handler.send(self.guild, content="audit"))
        self.channel.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
