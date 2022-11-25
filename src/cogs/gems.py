import discord
import re
import os
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
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='RANDOM GEM SELECTION', icon_url='attachment://prohibited.png')
            embed.add_field(name="**__Error__**", value="That's not a valid input. Please try again or `!help gems` for more information.", inline=False)

            if discord.ChannelType == "private":
                await ctx.message.author.send(file=icon, embed=embed)

            elif discord.ChannelType != "private":
                await ctx.send(file=icon, embed=embed)



    #----------------------------
    # Gems Command
    #----------------------------
    @commands.command(extras=[":gem:  **__Gems__**","**Usage: `!gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`n = number of gems to be generated`**\n"])
    async def gems(self, ctx, *, gemstring):
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
            #select = gemstring[0]
            i = int(gemstring[1])

            while i > 0:
                lines = open(os.path.dirname(__file__)+'./gems/'+gemstring[0]+'gp.txt').read().splitlines()
                randline = random.choice(lines)
                list = randline.split(";")
                m_Response = f'- {list[0]}: {list[1]}'
                gems.append(m_Response)
                i -= 1

            self.bot.logger.log(f"{ctx.message.author} found "+gemstring[1]+" x "+gemstring[0]+"gp gems.")
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/gem-stone.png'), filename='gem-stone.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url='attachment://gem-stone.png')
            embed.set_author(name = 'RANDOM GEM SELECTION')
            embed.add_field(name = 'You discovered the following '+gemstring[0]+'gp gems:', value = '\n'.join(gems), inline=False)


        else:
            self.bot.logger.log(f"{ctx.message.author} ({ctx.message.author.guild}) entered invalid argument")
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Gems)', icon_url='attachment://prohibited.png')
            embed.add_field(name='**__Error__**', value="That's not a valid input. Please try again or `!help gems` for more information.", inline=False)

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=icon, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=icon, embed=embed)

async def setup(bot):
    await bot.add_cog(Gems(bot))
