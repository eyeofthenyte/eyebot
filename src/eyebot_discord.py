import logging
import os, asyncio
import discord

from services.configService import ConfigService
from services.logService import LogService

from discord.ext import commands


#----------------------------
#Bot Core Setup
#----------------------------

config = ConfigService(os.path.dirname(__file__) + "/../config.yaml").get()
TOKEN = config["discord"]["bot_token"]

logger = LogService("discord", config["log_level"])
logger.log(config["prefix"])

BOT_PREFIX = "!"
if config["prefix"]:
    BOT_PREFIX = config["prefix"]

bot = commands.Bot(
    command_prefix = BOT_PREFIX,
    intents = discord.Intents.all()
)

bot.remove_command('help')

bot.logger = logger
bot.config = config

currDir = os.path.dirname(os.path.realpath(__file__))

async def load_extensions():
    #Listing Extensions
    for filename in os.listdir(currDir + '/cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            logger.info(f'Extension found: {filename[:-3]}')

#----------------------------
#Bot Events
#----------------------------

#Bot Startup
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('with the strings of fate.'))
    logger.info(f'{bot.user.name} has awoken!')
    logger.info(f'{bot.user.name} is connected to the following Discord Servers:')
    for guild in bot.guilds:
        logger.info(f'          (id: {guild.id})     -     {guild.name}')
    logger.info('End of Server Listing')
    return

#New Server Connection
@bot.event
async def on_guild_join(guild):
    bot_entry = await guild.audit_logs(action=discord.AuditLogAction.bot_add).flatten()
    try:
        await bot_entry[0].user.send("You see a small strange egg.\nTo see what it's about type `.help`")
    except:
        logger.error('connection_error - Could not send inital DM. User\'s DMs are closed. Bot still connected to server.')

    logger.info(f'connection_made - {bot.user.name} has been found in: {guild.name} (id: {guild.id})')


# Global Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logger.warn(f'Invalid command used: {ctx.message.content}')
        await ctx.send('That command does not exist.')
    elif isinstance(error, commands.MissingPermissions):
        logger.warn(f'{ctx.message.author} ({ctx.message.author.guild}) attempted to use command without required permissions.')
        await ctx.send("Sorry, you don't have the permissions to use that command.")
    if isinstance(error, commands.NotOwner):
        logger.warn(f'{ctx.message.author} ({ctx.message.author.guild}) attempted to use command without required permissions.')
        await ctx.send(f"{ctx.message.author}, sorry you need to be the bot owner to use that command.")


#----------------------------
#Bot Commands
#----------------------------

#Disconnect bot from server BOT OWNER ONLY
@bot.command()
@commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
async def leave(ctx, *, guild_name):
    guild = discord.utils.get(bot.guilds, name=guild_name)
    if guild is None:
        await ctx.send("I don't recognize that guild. Please enter the server name. (case sensitive)")
        logger.error(f'leaving_error - blank or invalid server name, please enter the guild name')
        return
    else:
        await guild.leave()
        logger.error(f'connection_broken: {bot.user.name} has left: {guild.name} (id: {guild.id})')

#Check connected servers BOT OWNER ONLY
@bot.command()
@commands.is_owner()
async def servers(ctx):
    for guild in bot.guilds:
        logger.info(f'%-10s(id: %s)%-5s-%-5s', ' ', guild.id, ' ', ' ', guild.name)
        await ctx.author.send(f'%-5s(id: %s)%-5s-%-5s%s', ' ', guild.id, ' ', ' ', guild.name)
    logger.info(f'-End of Server Listing-')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
