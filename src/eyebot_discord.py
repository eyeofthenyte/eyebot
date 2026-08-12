import logging
import os, asyncio
import discord

from adapters.discord_adapter import (
    DiscordTransportAdapter,
)
from core.cog_registry import build_portable_router
from core.command_model import ResponseVisibility
from services.logService import LogService
from services.platformConfigService import load_split_config, resolve_discord_prefix
from eyebot import send_reconcile_command, send_restart_command

from discord.ext import commands


# ----------------------------
# Bot Core Setup
# ----------------------------

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.getenv(
    "EYEBOT_CONFIG_PATH",
    os.path.join(project_root, "config.yaml"),
)
platform_config_path = os.getenv(
    "EYEBOT_PLATFORM_CONFIG_PATH",
    os.path.join(project_root, "platforms.yaml"),
)
guild_config_dir = os.getenv(
    "EYEBOT_GUILD_CONFIG_DIR",
    os.path.join(project_root, "data", "guilds"),
)

config, configService, platformConfigService = load_split_config(
    config_path,
    platform_config_path,
    guild_config_dir=guild_config_dir,
    legacy_roller_path=os.path.join(project_root, "src/cogs/roller/config.json"),
    legacy_clear_path=os.path.join(project_root, "src/cogs/clear/config.json"),
)

# print(f"Config loaded: {config}") <== for debugging

# Apply defaults
config.setdefault("discord", {})
config["discord"].setdefault("bot_token", "")
config.setdefault("prefix", "!")
config.setdefault("logging", {})

# Never accept or persist credentials through an interactive bot process.
if not config["discord"]["bot_token"]:
    raise RuntimeError(
        "Discord bot token is missing. Store it with "
        "`python src/manage_secrets.py set discord bot_token` and restart EyeBot."
    )

# Prompt for missing prefix
if not config.get("prefix"):
    config["prefix"] = input("Enter your desired bot prefix (default is '!'): ") or "!"
    global_config = configService.get()
    global_config["prefix"] = config["prefix"]
    configService.set(global_config)
    configService.save()

TOKEN = config["discord"]["bot_token"]
BOT_PREFIX = config["prefix"]

logger = LogService("discord", config["logging"])
logger.log(f"Prefix set to: {BOT_PREFIX}")


def prefix_for_discord_message(message):
    """Resolve a guild prefix, falling back to the global prefix for DMs."""
    return resolve_discord_prefix(
        platformConfigService,
        message,
        BOT_PREFIX,
    )


def discord_command_prefix(_bot, message):
    return prefix_for_discord_message(message)

# Use only necessary intents (recommended security practice)
#intents = discord.Intents.all()
intents = discord.Intents.default()
intents.message_content = True  # <- REQUIRED to read messages in servers
intents.messages = True
intents.guilds = True
intents.members = True  # If needed
intents.reactions = True  # Required for social-media approval reactions

bot = commands.Bot(
    command_prefix=discord_command_prefix,
    intents=intents
)

bot.remove_command('help')

bot.logger = logger
bot.config = config
bot.platform_config_service = platformConfigService
bot.platform_reconciler = send_reconcile_command
bot.platform_restarter = send_restart_command

currDir = os.path.dirname(os.path.realpath(__file__))

# ----------------------------
# Load Extensions
# ----------------------------
async def load_extensions():
    for filename in os.listdir(os.path.join(currDir, 'cogs')):
        if filename.endswith('.py'):
            ext = f'cogs.{filename[:-3]}'
            try:
                await bot.load_extension(ext)
                logger.info(f'Loaded extension: {ext}')
            except Exception as e:
                logger.error(f'Failed to load extension {ext}: {e}')
    bot.command_router = build_portable_router(bot.cogs, strict=True)
    bot.command_transport = DiscordTransportAdapter(
        bot.command_router,
        prefix=BOT_PREFIX,
        prefix_resolver=prefix_for_discord_message,
        destination_resolver=resolve_discord_destinations,
    )
    logger.info(
        "Registered platform-neutral commands: "
        + ", ".join(bot.command_router.registered_commands)
    )


async def resolve_discord_destinations(message, response):
    """Apply Discord-only private/blind delivery policy at the transport edge."""
    if response.visibility == ResponseVisibility.PUBLIC:
        return (message.channel,)
    if message.guild is None:
        return (message.author,) if response.visibility != ResponseVisibility.BLIND else ()

    roller = bot.get_cog("Roll")
    guild_config = (
        roller.config.get(str(message.guild.id), {})
        if roller is not None
        else {}
    )
    dm_channel_id = guild_config.get("dm_channel", "UNSET")
    if dm_channel_id != "UNSET":
        destination = bot.get_channel(int(dm_channel_id))
        if destination is not None:
            return (destination,)

    if response.visibility == ResponseVisibility.REQUESTER:
        user_channel_id = guild_config.get("user_channels", {}).get(
            str(message.author.id)
        )
        if user_channel_id:
            destination = bot.get_channel(int(user_channel_id))
            if destination is not None:
                return (destination,)
        return (message.author,)

    dm_role_name = guild_config.get("dm_role", "UNSET")
    role = (
        discord.utils.get(message.guild.roles, name=dm_role_name)
        if dm_role_name != "UNSET"
        else None
    )
    if role is None:
        return ()
    return tuple(
        member for member in role.members
        if member.id != message.author.id
    )


# ----------------------------
# Bot Events
# ----------------------------
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game('with the strings of fate.')
    )
    logger.info(f'{bot.user.name} has awoken!')
    logger.info(f'{bot.user.name} is connected to the following Discord Servers:')
    for guild in bot.guilds:
        logger.info(f'  (id: {guild.id}) - {guild.name}')
    logger.info('End of Server Listing')


@bot.event
async def on_message(message):
    message_prefix = prefix_for_discord_message(message)
    if message.author.bot or not message.content.strip().startswith(message_prefix):
        return

    transport = getattr(bot, "command_transport", None)
    if transport is None or not await transport.dispatch(message):
        await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    platformConfigService.ensure_discord_guild(
        str(guild.id),
        guild.name,
        BOT_PREFIX,
    )
    platformConfigService.save_discord_guild(guild.id)
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
            adder = entry.user
            await adder.send("You see a small strange egg.\nTo see what it's about type `.help`")
            break
    except Exception as e:
        logger.error(f'connection_error - Could not send initial DM. Reason: {e}')

    logger.info(f'connection_made - {bot.user.name} has been found in: {guild.name} (id: {guild.id})')


# ----------------------------
# Global Error Handler
# ----------------------------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logger.warning(f'Invalid command used: {ctx.message.content}')
        await ctx.send('❌ That command does not exist.')
        return

    elif isinstance(error, commands.MissingPermissions):
        logger.warning(f'{ctx.author} tried using a command without required permissions in {ctx.guild}.')
        await ctx.send("⛔ You don’t have the necessary permissions to use that command.")
        return

    elif isinstance(error, commands.NotOwner):
        logger.warning(f'{ctx.author} attempted to use an owner-only command in {ctx.guild}.')
        await ctx.send("🔒 Only the bot owner can use that command.")
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ You're missing a required argument for this command.")
        return

    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ One of your arguments was invalid or in the wrong format.")
        return

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ That command is on cooldown. Try again in {round(error.retry_after, 2)}s.")
        return

    # Fallback for unexpected errors
    logger.error(f"❗ Unexpected error in command '{ctx.command}': {type(error).__name__} - {error}")
    await ctx.send("🚨 An unexpected error occurred. Please contact an admin or try again later.")
    return  # <-- critical: ends propagation


# ----------------------------
# Main Entrypoint
# ----------------------------
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
