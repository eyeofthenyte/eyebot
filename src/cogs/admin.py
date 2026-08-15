import asyncio

import discord
from discord.ext import commands
from eyebot import send_restart_command

# ---------------------------------------------------------
# Admin Commands
# ---------------------------------------------------------
class Admin (commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]


    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Core functions started.")

    async def cog_command_error(self, ctx, error):
        self.logger.error(f'Admin encountered error: {error}')
        if isinstance(error, commands.CommandError):
            self.logger.error("There was an error with Admin commands.")
            await ctx.send('Something went wrong.')



    # ---------------------------------------------------------
    # Administrative Commands
    # ---------------------------------------------------------
    @commands.command(name="setprefix")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx, prefix: str):
        """Set this server's prefix, or use ``reset`` for the global default."""
        if ctx.guild is None:
            return await ctx.send("❌ Server prefixes cannot be changed in DMs.")

        global_prefix = self.config.get("prefix", "!") or "!"
        if prefix.casefold() == "reset":
            selected_prefix = global_prefix
        else:
            selected_prefix = prefix.strip()
            if not 1 <= len(selected_prefix) <= 5 or any(
                character.isspace() for character in selected_prefix
            ):
                return await ctx.send(
                    "❌ Prefixes must contain 1–5 non-whitespace characters."
                )

        platform_service = getattr(
            self.bot,
            "platform_config_service",
            None,
        )
        if platform_service is None:
            return await ctx.send("❌ Per-server configuration is unavailable.")

        guild_config = platform_service.ensure_discord_guild(
            str(ctx.guild.id),
            ctx.guild.name,
            global_prefix,
        )
        guild_config["prefix"] = selected_prefix
        platform_service.save_discord_guild(ctx.guild.id)
        await ctx.send(
            f"✅ Server command prefix set to `{selected_prefix}`."
        )

    #Shutdown bot
    @commands.command(aliases=['shutdown','sd'])
    @commands.is_owner()
    async def _shutdown(self,ctx):
        """
        🔒 Gracefully shuts down the bot.

        Usage:
        `!shutdown`

        Aliases:`!sd`, `!_shutdown`
        
        Access: Bot Owner Only
        """


        try:
            await ctx.send("Shutting down the bot...")
            await self.bot.close()

        except Exception as e:
            self.bot.logger.log(f'{e}')     
            await ctx.send("There was a problem shutting down the bot. You might not be the bot owner.")

    @commands.command(name="restart")
    @commands.is_owner()
    async def restart_platform(self, ctx, platform: str):
        """
        🔒 Restarts one enabled platform bot.

        Usage:
        `!restart <platform>`

        Example:
        `!restart twitch`

        Access: Bot Owner Only
        """
        platform = platform.strip().lower()
        if platform == "discord":
            await ctx.send("♻️ Restarting the Discord bot...")
        try:
            result = await asyncio.to_thread(send_restart_command, platform)
        except (OSError, RuntimeError, ValueError) as error:
            if platform != "discord":
                await ctx.send(f"❌ Restart failed: {error}")
            self.logger.error(f"Platform restart failed for {platform}: {error}")
            return
        if platform != "discord":
            await ctx.send(f"✅ {result}.")

    #Disconnect bot from server BOT OWNER ONLY
    @commands.command()
    @commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
    async def leave(self, ctx, *, guild_name):
        """
        📤 Forces the bot to leave a server by its name.

        Usage:
        `!leave <Server Name>`

        Example:
        `!leave My Cool Server`

        Note: Server name is case-sensitive
        Access: Server Administrator or Bot Owner
        """

        guild = discord.utils.get(self.bot.guilds, name=guild_name)
        if guild is None:
            await ctx.send("I don't recognize that guild. Please enter the server name. (case sensitive)")
            self.logger.error(
                "leaving_error - blank or invalid server name, "
                "please enter the guild name"
            )
            return
        else:
            await guild.leave()
            self.logger.info(
                f"connection_broken: {self.bot.user.name} has left: "
                f"{guild.name} (id: {guild.id})",
                guild_id=guild.id,
            )

    #Check connected servers BOT OWNER ONLY
    @commands.command(name="servers", aliases=["server"])
    @commands.is_owner()
    async def servers(self, ctx):
        """
        📋 Lists all servers the bot is currently connected to via DM.\n"

        Usage:
        `!servers` or `!server`

        Access: Bot Owner Only
        """

        guilds = tuple(self.bot.guilds)
        if not guilds:
            await ctx.author.send("EyeBot is not currently connected to any servers.")
            self.logger.info("End of Server Listing - no connected servers.")
            return

        platform_names = (
            "discord",
            "twitch",
            "youtube",
            "facebook",
            "kick",
            "twitter",
            "bluesky",
            "tiktok",
            "instagram",
            "substack",
            "kofi",
        )
        platform_service = getattr(
            self.bot,
            "platform_config_service",
            None,
        )
        lines = ["📋 **Connected Servers**"]
        for guild in guilds:
            line = f"• {guild.name} (id: {guild.id})"
            lines.append(line)
            self.logger.info(line)

            statuses = []
            for platform_name in platform_names:
                if platform_service is not None:
                    platform_config = platform_service.effective_guild_platform(
                        guild.id,
                        platform_name,
                    )
                else:
                    platform_config = getattr(self, "config", {}).get(
                        platform_name,
                        {},
                    )
                enabled = (
                    isinstance(platform_config, dict)
                    and platform_config.get("enabled") is True
                )
                statuses.append(
                    f"{platform_name}: {'enabled' if enabled else 'disabled'}"
                )
            lines.append("  Platforms: " + " | ".join(statuses))

        try:
            pages = []
            page = ""
            for line in lines:
                candidate = f"{page}\n{line}" if page else line
                if len(candidate) > 1900:
                    pages.append(page)
                    page = line
                else:
                    page = candidate
            if page:
                pages.append(page)
            for page in pages:
                await ctx.author.send(page)
        except discord.Forbidden:
            await ctx.send(
                "I couldn't send you the server list. Please enable direct "
                "messages and try again."
            )
            return

        await ctx.send("✅ I sent the connected server list by direct message.")
        self.logger.info("End of Server Listing.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
