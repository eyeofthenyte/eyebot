import discord
import re
import random
import logging
from services.logService import LogService
from discord.ext import commands

# ---------------------------------------------------------
# Found Gems Generator
# ---------------------------------------------------------
class Gems(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Staring at the shinies.')

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'missing or invalid argument for gems')
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Gems)', icon_url='attachment://prohibited.png')
            embed.add_field(name=':gem:  **__Gems__**', value='**Usage: `{self.prefix}gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`     n = number of gems to be generated`**\n The value of gems corresponds to the Gem Tables DMG - Chapter 7.\nThis will generate a number of gems of a single gold value type based the table selected.', inline=False)

            if discord.ChannelType == "private":
                await ctx.message.author.send(file=file, embed=embed)
                return
            elif discord.ChannelType != "private":
                await ctx.send(file=file, embed=embed)
                return


    #----------------------------
    # Gems Command
    #----------------------------
    @commands.command()
    async def gems(self, ctx, *, gemstring):
        await ctx.message.delete()
        #----------------------------
        # Variables
        #----------------------------
        m_Response = ""
        randline = ""
        ckstr = bool(re.search(r"\s", gemstring))
        lstr = len(gemstring)
        gems=[]

        #----------------------------
        # Gem Table Selection
        #----------------------------
        if ckstr == True:
            gemstring = gemstring.split()
            select = gemstring[0]
            i = int(gemstring[1])
            while i > 0:
                lines = open(os.path.join(os.path.dirname(__file__), f"./gems/{select}gp.txt")).read().splitlines()
                randline = random.choice(lines)
                list = randline.split(";")
                m_Response = f'- {list[0]}: {list[1]}'
                gems.append(m_Response)
                i -= 1

            file = discord.File('./eyebot/images/commands/gem-stone.png', filename='gem-stone.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url='attachment://gem-stone.png')
            embed.set_author(name = 'RANDOM GEM SELECTION')
            embed.add_field(name = 'You discovered the following {select} gems:', value = '\n'.join(gems), inline=False)

            if discord.ChannelType == "private":
                await ctx.message.author.send(file=file, embed=embed)
            elif discord.ChannelType != "private":
                await ctx.send(file=file, embed=embed)

        else:
            if lstr == 1 and gemstring == '?':
                self.bot.logger.log(f"{ctx.message.author}({ctx.message.author.guild}) asked for help with .gems command")
                file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
                embed = discord.Embed(color=0x019cd0)
                embed.set_author(name='Help (Gems)', icon_url='attachment://warning.png')
                embed.add_field(name=':gem:  **__Gems__**', value='**Usage: `{self.prefix}gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`     n = number of gems to be generated`**\n The value of gems corresponds to the Gem Tables DMG - Chapter 7.\nThis will generate a number of gems of a single gold value type based the table selected.', inline=False)
                if discord.ChannelType == "private":
                    await ctx.message.author.send(file=file, embed=embed)
                elif discord.ChannelType != "private":
                    await ctx.send(file=file, embed=embed)

            else:
                self.bot.logger.log(" : ({ctx.message.author.guild}) entered invalid argument")
                file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
                embed = discord.Embed(color=0x019cd0)
                embed.set_author(name='Help (Gems)', icon_url='attachment://prohibited.png')
                embed.add_field(name=':gem:  **__Gems__**', value='**Usage: `{self.prefix}gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`     n = number of gems to be generated`**\n The value of gems corresponds to the Gem Tables DMG - Chapter 7.\nThis will generate a number of gems of a single gold value type based the table selected.', inline=False)
                if discord.ChannelType == "private":
                    await ctx.message.author.send(file=file, embed=embed)
                elif discord.ChannelType != "private":
                    await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Gems(bot))
