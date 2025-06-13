import logging
import os, asyncio
import discord

from services.configService import ConfigService
from services.logService import LogService

from discord.ext import commands


# ----------------------------
# Bot Core Setup
# ----------------------------

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))

configService = ConfigService(config_path)
config = configService.get()

# print(f"Config loaded: {config}") <== for debugging

# Apply defaults
config.setdefault("discord", {})
config["discord"].setdefault("bot_token", "")
config.setdefault("prefix", "!")
config.setdefault("logging", {})

# Prompt for missing token
if not config["discord"]["bot_token"]:
    config["discord"]["bot_token"] = input("Enter your Discord bot token: ")
    configService.set(config)  # Save back if supported
    configService.save()       # saves it to disk

# Prompt for missing prefix
if not config.get("prefix"):
    config["prefix"] = input("Enter your desired bot prefix (default is '!'): ") or "!"
    configService.set(config)
    configService.save()

TOKEN = config["discord"]["bot_token"]
BOT_PREFIX = config["prefix"]

logger = LogService("discord", config["logging"])
logger.log(f"Prefix set to: {BOT_PREFIX}")

# Use only necessary intents (recommended security practice)
#intents = discord.Intents.all()
intents = discord.Intents.default()
intents.message_content = True  # <- REQUIRED to read messages in servers
intents.messages = True
intents.guilds = True
intents.members = True  # If needed

bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents
)

bot.remove_command('help')

bot.logger = logger
bot.config = config

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
async def on_guild_join(guild):
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
