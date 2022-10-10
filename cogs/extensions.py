import eyebot_discord
import os, datetime
from discord.ext import commands

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

#Pass Bot Prefix
def get_prefix():
    data = open(os.path.join(os.path.dirname(__file__), "../eyebot.cfg")).read().splitlines()
    prefix = data[1]
    return prefix
    data.close()

prefix = get_prefix()

# ---------------------------------------------------------
# Extension Related Commands
# ---------------------------------------------------------
class Extensions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Has made external connections.')


    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Missing argument')
            print(f'{t()}: missing argument')
            return


    #----------------------------
    # Gems Command
    #----------------------------

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            self.bot.load_extension(f'cogs.{extension}')
            print(f'{t()}: Loaded extension - "{extension}"')
            file = discord.File('./eyebot/images/commands/thumbs-up.png', filename='thumbs-up.png')
            embed = discord.Embed(color=0x01f31d)
            embed.set_author(name = 'LOADED ' + extension.upper(), icon_url = 'attachment://thumbs-up.png')
            embed.add_field(name = '**__Extension Load__**', value = 'Extension: "' + extension + '" has been loaded successfully.', inline=False)
        except Exception as e:
            print(f'{t()}: {e}')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name = 'LOADING ' + extension.upper() + ' FAILED', icon_url = 'attachment://warning.png')
            embed.add_field(name = '**__Extension Load__**', value = e, inline=False)
        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:
            self.bot.unload_extension(f'cogs.{extension}')
            print(f'{t()}: Unloaded extension - "{extension}"')
            file = discord.File('./eyebot/images/commands/thumbs-up.png', filename='thumbs-up.png')
            embed = discord.Embed(color=0x01f31d)
            embed.set_author(name = 'UNLOADED ' + extension.upper(), icon_url = 'attachment://thumbs-up.png')
            embed.add_field(name = '**__Extension Unload__**', value = 'Extension: "' + extension + '" has been unloaded.', inline=False)
        except Exception as e:
            print(f'{t()}: {e}')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name = 'UNLOADING ' + extension.upper() + ' FAILED', icon_url = 'attachment://warning.png')
            embed.add_field(name = '**__Extension Unload__**', value =  e, inline=False)
        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        print(f'{t()}: Attempting to reload {extension}')
        try:
            try:
                self.bot.unload_extension(f'cogs.{extension}')
                print(f'    - "{extension}" has been unloaded.')
            except Exception as e:
                print(f'    - {e}')
            try:
                self.bot.load_extension(f'cogs.{extension}')
                print(f'    - "{extension}" has been loaded.')
                file = discord.File('./eyebot/images/commands/thumbs-up.png', filename='thumbs-up.png')
                embed = discord.Embed(color=0x01f31d)
                embed.set_author(name = 'RELOADED ' + extension.upper(), icon_url = 'attachment://thumbs-up.png')
                embed.add_field(name = '**__Extension Reload__**', value='Reloading "' + extension + '" has been completed successfully.', inline=False)
                print(f'{t()}: Reloaded extension - "{extension}" successfully.')

            except Exception as e:
                print(f'    - {e}')
                print(f'{t()}: Reload extension - "{extension}" has failed.')
                file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
                embed = discord.Embed(color=0xcc0000)
                embed.set_author(name = 'RELOADING ' + extension.upper() + ' FAILED', icon_url = 'attachment://warning.png')
                embed.add_field(name = '**__Extension Reload__**', value='Reloading "' + extension + '" has failed. Invalid extension or extension not loaded.', inline=False)

        except Exception as e:
            print(f'{t()}: {e}')
        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

def setup(bot):
    bot.add_cog(Extensions(bot))
