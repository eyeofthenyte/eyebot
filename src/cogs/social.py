"""Discord commands and moderator reaction approvals for social posts."""

from __future__ import annotations

import re

import discord
from discord.ext import commands

from core.social_reactions import enabled_reaction_emojis
from services.platformJobService import DuplicateJobError
from services.socialPostingService import SocialPostRequest, SocialPostingService


REACTION_PLATFORMS = {
    "🐦": "twitter",
    "🦋": "bluesky",
    "📘": "facebook",
    "📸": "instagram",
    "🎵": "tiktok",
    "📣": "all",
}
CANCEL_REACTION = "❌"
SUCCESS_REACTION = "✅"
FAILURE_REACTION = "⚠️"
HTTPS_URL = re.compile(r"https://[^\s<>]+", re.IGNORECASE)
SOCIAL_REACTION_HELP = """**Approval reactions in `socialmedia_sources`:**
🐦 **Twitter/X** — queue the attached images and caption for Twitter/X.
🦋 **Bluesky** — queue the attached images and caption for Bluesky.
📘 **Facebook** — queue the attached images and caption for Facebook.
📸 **Instagram** — host attached images temporarily, or use a public HTTPS image URL.
🎵 **TikTok** — host attached photos temporarily, or use a verified public HTTPS media URL.
📣 **All compatible** — queue attached images for every compatible ready account.
❌ **Cancel** — cancel pending jobs created from that source message.
✅ **Success** — EyeBot queued or cancelled the requested jobs.
⚠️ **Failed** — EyeBot could not queue or cancel the requested jobs.

EyeBot only adds platform placeholders for accounts that are enabled, connected, and have posting enabled. Only moderators can approve them."""
PUBLIC_MEDIA_PROVIDER_HELP = """**Public-media provider notation:**
🏠 `local_caddy` — **implemented**; stores temporary files in EyeBot's Docker volume and serves them through the gateway behind Caddy.
☁️ `cloudflare_r2` — placeholder for an R2 bucket, S3 endpoint, custom media domain, access-key ID, and secret key.
🪣 `amazon_s3` — placeholder for an S3 bucket, AWS region, public/signed URL base, access-key ID, and secret key.
🔷 `azure_blob` — placeholder for an Azure storage account, container, public URL base, and SAS or service credential.
🌐 `google_cloud_storage` — placeholder for a GCS project, bucket, public URL base, and service-account credential.

Select with `public_media.provider`. Cloud credentials must use EyeBot's encrypted secret store, never guild YAML or Discord. Cloud providers are documented placeholders and are not active until their storage adapters are implemented."""


class Social(commands.Cog):
    """Queue guild-authorized outbound social posts."""

    def __init__(self, bot):
        self.bot = bot
        self.posting = SocialPostingService(
            bot.platform_config_service,
            getattr(bot, "config", {}),
        )

    @commands.command(
        name="socialpost",
        extras=[
            "📣 **Social Post**",
            "**Usage:** `!socialpost <twitter|facebook|bluesky|all> <text>`\n\n"
            + SOCIAL_REACTION_HELP,
            PUBLIC_MEDIA_PROVIDER_HELP,
        ],
    )
    @commands.has_permissions(manage_guild=True)
    async def social_post(self, ctx, platform: str, *, text: str):
        """Queue a text post: !socialpost <platform|all> <text>."""
        if not self._is_mod_channel(ctx):
            return await ctx.send(
                "❌ Social posts must be queued in the configured mod channel."
            )
        request = SocialPostRequest(
            guild_id=str(ctx.guild.id),
            platform=platform,
            text=text,
            source_message_id=str(ctx.message.id),
            requested_by=str(ctx.author.id),
        )
        await self._queue_command(ctx, request)

    @commands.command(
        name="socialmedia",
        extras=[
            "🖼️ **Social Media**",
            "**Usage:** `!socialmedia <twitter|facebook|bluesky|instagram|tiktok|all> [caption]` "
            "with one to four attached images, or reply to a message containing images.\n\n"
            + SOCIAL_REACTION_HELP,
            PUBLIC_MEDIA_PROVIDER_HELP,
        ],
    )
    @commands.has_permissions(manage_guild=True)
    async def social_media(self, ctx, platform: str, *, text: str = ""):
        """Post attached/replied images: !socialmedia <platform|all> [caption]."""
        if not self._is_source_channel(ctx):
            return await ctx.send(
                "❌ Image posts must be queued in the configured "
                "`socialmedia_sources` channel."
            )
        attachments = list(getattr(ctx.message, "attachments", ()) or ())
        reference = getattr(ctx.message, "reference", None)
        referenced = getattr(reference, "resolved", None)
        if not attachments and referenced is not None:
            attachments = list(getattr(referenced, "attachments", ()) or ())
        if not attachments:
            return await ctx.send(
                "❌ Attach images to this command or reply to a message containing images."
            )
        request = SocialPostRequest(
            guild_id=str(ctx.guild.id),
            platform=platform,
            text=text,
            source_message_id=str(ctx.message.id),
            requested_by=str(ctx.author.id),
            attachments=tuple(attachments),
        )
        await self._queue_command(ctx, request)

    @commands.command(
        name="socialurl",
        extras=[
            "🔗 **Social URL**",
            "**Usage:** `!socialurl <instagram|tiktok> <https-media-url> [caption]`\n\n"
            + SOCIAL_REACTION_HELP,
            PUBLIC_MEDIA_PROVIDER_HELP,
        ],
    )
    @commands.has_permissions(manage_guild=True)
    async def social_url(
        self,
        ctx,
        platform: str,
        media_url: str,
        *,
        text: str = "",
    ):
        """Queue URL media: !socialurl <instagram|tiktok> <https-url> [caption]."""
        if not (self._is_source_channel(ctx) or self._is_mod_channel(ctx)):
            return await ctx.send(
                "❌ Run this command in the configured social-media source or mod channel."
            )
        request = SocialPostRequest(
            guild_id=str(ctx.guild.id),
            platform=platform,
            text=text,
            source_message_id=str(ctx.message.id),
            requested_by=str(ctx.author.id),
            media_url=media_url,
        )
        await self._queue_command(ctx, request)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Seed posting reactions on media placed in the guild source channel."""
        guild = getattr(message, "guild", None)
        author = getattr(message, "author", None)
        if guild is None or getattr(author, "bot", False):
            return
        service = self.bot.platform_config_service
        guild_config = service.discord_guilds().get(str(guild.id), {})
        if str(getattr(message.channel, "id", "")) != str(
            guild_config.get("socialmedia_sources_channel")
        ):
            return
        context = await self.bot.get_context(message)
        if getattr(context, "valid", False):
            return
        attachments = tuple(getattr(message, "attachments", ()) or ())
        has_media_url = HTTPS_URL.search(str(getattr(message, "content", "") or "")) is not None
        emojis = enabled_reaction_emojis(
            service,
            str(guild.id),
            REACTION_PLATFORMS,
            has_attachments=bool(attachments),
            has_media_url=has_media_url,
            attachments_can_be_hosted=self.posting.public_media.enabled,
            attachment_content_types=tuple(
                str(getattr(item, "content_type", "") or "").casefold()
                for item in attachments
            ),
        )
        for emoji in emojis:
            await self._mark(message, emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Treat moderator reactions in the source channel as posting approval."""
        bot_user = getattr(self.bot, "user", None)
        if payload.guild_id is None or payload.user_id == getattr(bot_user, "id", None):
            return
        emoji = str(payload.emoji)
        if emoji not in {*REACTION_PLATFORMS, CANCEL_REACTION}:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        service = self.bot.platform_config_service
        guild_config = service.discord_guilds().get(str(guild.id), {})
        if str(payload.channel_id) != str(guild_config.get("socialmedia_sources_channel")):
            return
        member = guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return
        if not getattr(member.guild_permissions, "manage_guild", False):
            return
        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
        if emoji == CANCEL_REACTION:
            removed = self.posting.cancel(str(guild.id), str(message.id))
            await self._mark(message, SUCCESS_REACTION if removed else FAILURE_REACTION)
            if removed:
                await channel.send(
                    f"🛑 Cancelled {removed} pending social post job(s).",
                    reference=message,
                    mention_author=False,
                )
            return

        platform = REACTION_PLATFORMS[emoji]
        attachments = tuple(getattr(message, "attachments", ()) or ())
        text = str(getattr(message, "content", "") or "").strip()
        media_url = None
        if platform in {"twitter", "facebook", "bluesky", "all"} and not attachments:
            await self._mark(message, FAILURE_REACTION)
            await channel.send(
                "❌ This approval reaction requires one to four attached images.",
                reference=message,
                mention_author=False,
            )
            return
        if platform in {"instagram", "tiktok"}:
            match = HTTPS_URL.search(text)
            if match and not attachments:
                media_url = match.group(0).rstrip(".,);]")
                text = (text[: match.start()] + text[match.end() :]).strip()
        request = SocialPostRequest(
            guild_id=str(guild.id),
            platform=platform,
            text=text,
            source_message_id=str(message.id),
            requested_by=str(member.id),
            attachments=attachments,
            media_url=media_url,
        )
        try:
            result = await self.posting.queue(request)
        except (DuplicateJobError, OSError, ValueError) as error:
            await self._mark(message, FAILURE_REACTION)
            await channel.send(
                f"❌ Social post was not queued: {error}.",
                reference=message,
                mention_author=False,
            )
            return
        await self._mark(message, SUCCESS_REACTION)
        await channel.send(
            "✅ Queued social post for " + ", ".join(result.queued) + ".",
            reference=message,
            mention_author=False,
        )

    async def _queue_command(self, ctx, request):
        try:
            result = await self.posting.queue(request)
        except (DuplicateJobError, OSError, ValueError) as error:
            return await ctx.send(f"❌ Social post was not queued: {error}.")
        await self._delete_invocation(ctx)
        await ctx.send(f"✅ Queued {len(result.queued)} social post job(s).")

    def _guild_config(self, ctx):
        if ctx.guild is None:
            return None
        return self.bot.platform_config_service.discord_guilds().get(
            str(ctx.guild.id), {}
        )

    def _is_mod_channel(self, ctx):
        config = self._guild_config(ctx)
        return config is not None and str(getattr(ctx.channel, "id", "")) == str(
            config.get("mod_channel")
        )

    def _is_source_channel(self, ctx):
        config = self._guild_config(ctx)
        return config is not None and str(getattr(ctx.channel, "id", "")) == str(
            config.get("socialmedia_sources_channel")
        )

    @staticmethod
    async def _mark(message, emoji):
        try:
            await message.add_reaction(emoji)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @staticmethod
    async def _delete_invocation(ctx):
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass


async def setup(bot):
    await bot.add_cog(Social(bot))
