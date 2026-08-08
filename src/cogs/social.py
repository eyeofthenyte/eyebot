"""Queue guild-authorized outbound social posts."""

from __future__ import annotations

import discord
from discord.ext import commands
from urllib.parse import urlparse

from services.platformJobService import PlatformJobService
from services.mediaStagingService import MediaStagingService


TEXT_POSTING_PLATFORMS = ("facebook", "twitter", "bluesky")
IMAGE_POSTING_PLATFORMS = ("twitter", "facebook", "bluesky")


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        service = bot.platform_config_service
        self.jobs = PlatformJobService(service.guild_config_dir / ".platform_jobs")
        self.media = MediaStagingService(
            service.guild_config_dir / ".platform_media"
        )

    @commands.command(name="socialpost")
    @commands.has_permissions(manage_guild=True)
    async def social_post(self, ctx, platform: str, *, text: str):
        """Queue a text post: !socialpost <platform|all> <text>."""
        if ctx.guild is None:
            return await ctx.send("❌ Run this command in the server's mod channel.")
        service = self.bot.platform_config_service
        guild_config = service.discord_guilds().get(str(ctx.guild.id), {})
        if getattr(ctx.channel, "id", None) != guild_config.get("mod_channel"):
            return await ctx.send("❌ Social posts must be queued in the configured mod channel.")
        selected = platform.casefold()
        platforms = TEXT_POSTING_PLATFORMS if selected == "all" else (selected,)
        if any(item not in TEXT_POSTING_PLATFORMS for item in platforms):
            return await ctx.send("❌ Select facebook, twitter, bluesky, or all. Use `socialurl` for Instagram/TikTok.")
        if not 1 <= len(text) <= 2000:
            return await ctx.send("❌ Post text must contain 1-2000 characters.")
        queued = []
        for item in platforms:
            settings = service.effective_guild_platform(ctx.guild.id, item)
            if settings.get("enabled") is True and settings.get("posting_enabled") is True:
                queued.append(self.jobs.enqueue(ctx.guild.id, item, "post", {"text": text}))
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
        if not queued:
            return await ctx.send("❌ None of the selected platforms has posting enabled.")
        await ctx.send(f"✅ Queued {len(queued)} social post job(s).")

    @commands.command(name="socialmedia")
    @commands.has_permissions(manage_guild=True)
    async def social_media(self, ctx, platform: str, *, text: str = ""):
        """Post attached/replied images: !socialmedia <platform|all> [caption]."""
        if ctx.guild is None:
            return await ctx.send("❌ Run this command in the server's mod channel.")
        service = self.bot.platform_config_service
        guild_config = service.discord_guilds().get(str(ctx.guild.id), {})
        source_channel = guild_config.get("socialmedia_sources_channel")
        if getattr(ctx.channel, "id", None) != source_channel:
            return await ctx.send(
                "❌ Image posts must be queued in the configured "
                "`socialmedia_sources` channel."
            )
        selected = platform.casefold()
        supported = IMAGE_POSTING_PLATFORMS
        selected_platforms = IMAGE_POSTING_PLATFORMS if selected == "all" else (selected,)
        if any(item not in supported for item in selected_platforms):
            return await ctx.send(
                "❌ Select twitter, facebook, bluesky, or all."
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
        queued = []
        for item in selected_platforms:
            settings = service.effective_guild_platform(ctx.guild.id, item)
            if settings.get("enabled") is not True or settings.get("posting_enabled") is not True:
                continue
            try:
                staged = await self.media.stage_images(
                    item, attachments, alt_text=text
                )
            except (OSError, ValueError) as error:
                return await ctx.send(f"❌ Unable to stage images: {error}")
            queued.append(
                self.jobs.enqueue(
                    ctx.guild.id,
                    item,
                    "image_post",
                    {"text": text[:2000], "media": staged},
                )
            )
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
        if not queued:
            return await ctx.send("❌ None of the selected platforms has image posting enabled.")
        await ctx.send(f"✅ Queued {len(queued)} image post job(s).")

    @commands.command(name="socialurl")
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
        if ctx.guild is None:
            return await ctx.send("❌ Run this command in the social-media source channel.")
        service = self.bot.platform_config_service
        guild_config = service.discord_guilds().get(str(ctx.guild.id), {})
        if getattr(ctx.channel, "id", None) not in {
            guild_config.get("socialmedia_sources_channel"),
            guild_config.get("mod_channel"),
        }:
            return await ctx.send(
                "❌ Run this command in the configured social-media source or mod channel."
            )
        selected = platform.casefold()
        parsed = urlparse(media_url)
        if (
            selected not in {"instagram", "tiktok"}
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return await ctx.send(
                "❌ Select Instagram/TikTok and provide a public HTTPS media URL."
            )
        settings = service.effective_guild_platform(ctx.guild.id, selected)
        if settings.get("enabled") is not True or settings.get("posting_enabled") is not True:
            return await ctx.send(f"❌ {selected} posting is disabled for this server.")
        self.jobs.enqueue(
            ctx.guild.id,
            selected,
            "post",
            {"text": text[:2000], "media_url": media_url},
        )
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
        await ctx.send(f"✅ Queued a `{selected}` media URL job.")


async def setup(bot):
    await bot.add_cog(Social(bot))
