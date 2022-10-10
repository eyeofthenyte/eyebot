import os, datetime
import discord
import yaml

from discord.ext import commands
from yaml.loader import SafeLoader

#----------------------------
#Bot Core Setup
#----------------------------
def read_cfg():
    with open('config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        return data

config = read_cfg()
TOKEN = config["discord"]["bot_token"]

BOT_PREFIX = "!"
if config["prefix"]:
    BOT_PREFIX = config["prefix"]

bot = commands.Bot(
    command_prefix = BOT_PREFIX,
    intents = discord.Intents()
)
bot.remove_command('help')

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

currDir = os.path.dirname(os.path.realpath(__file__))

#Listing Extensions
for filename in os.listdir(currDir + '/../cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        print(f'{t()}: Extension found - {filename[:-3]}')

#----------------------------
#Bot Events
#----------------------------

#Bot Startup
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('with the strings of fate.'))
    print(f"{t()}: {bot.user.name} has awoken!")
    print(F'{t()}: {bot.user.name} is connected to the following Discord Servers:')
    for guild in bot.guilds:
        print(f'     (id: {guild.id})    -    {guild.name}')
    print(f'\n     -End of Server Listing-\n')
    return

#New Server Connection
@bot.event
async def on_guild_join(guild):
    bot_entry = await guild.audit_logs(action=discord.AuditLogAction.bot_add).flatten()
    try:
        await bot_entry[0].user.send("You see a small strange egg.\nTo see what it's about type `.help`")
    except:
        print(f"{t()}: connection_error - Could not send inital DM. User's DMs are closed. Bot still connected to server.")

    print(f'{t()}: connection_made - {bot.user.name} has been found in: {guild.name}(id: {guild.id})')

#Bot Left Server
#@bot.event
#async def on_guild_remove(guild):

# Global Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f'{t()}: Invalid command used: ' + f' {ctx.message.content}' )
        await ctx.send('That command does not exist.')
    elif isinstance(error, commands.MissingPermissions):
        print(f'{t()}: {ctx.message.author({ctx.message.author.guild})} attempted to use command without required permissions.')
        await ctx.send("Sorry, you don't have the permissions to use that command.")
    if isinstance(error, commands.NotOwner):
        print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) attempted to use command without required permissions.')
        await ctx.send("{ctx.message.author}, sorry you need to be the bot owner to use that command.")


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
        print(f'{t()}: leaving_error - blank or invalid server name, please enter the guild name')
        return
    else:
        await guild.leave()
        print(f'{t()}: connection_broken: {bot.user.name} has left: {guild.name}(id: {guild.id})')

#Check connected servers BOT OWNER ONLY
@bot.command()
@commands.is_owner()
async def servers(ctx):
    for guild in bot.guilds:
        print(f'     (id: {guild.id})    -    {guild.name}')
        await ctx.author.send(f'     (id: {guild.id})    -    {guild.name}')
    print(f'\n     -End of Server Listing-')


bot.run(TOKEN)


