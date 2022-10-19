import discord
import random
import os
import logging
from services.logService import LogService
from discord.ext import commands

# ---------------------------------------------------------
# Wild Magic Surge Generator
# ---------------------------------------------------------
class WildMagic(commands.Cog):

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
        self.bot.logger.log(f'Magic is getting chaotic.')


    #----------------------------
    # Wild Magic Surge
    #----------------------------
    @commands.command(aliases=['wildmagic', 'wm', 'surge'], extras=["f':sparkles:  **__WildMagic__**'", "f'**Usage: `{self.prefix}wildmagic #`\n other aliases `{self.prefix}wm, {self.prefix}surge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!\n'", "inline=False"])
    async def _wildmagic(self, ctx, *, select):

        if select == '1':
            try:
               lines = open(os.path.join(os.path.dirname(__file__), 'wildmagic/randommagicaleffects2.0.txt')).read().splitlines()
               self.bot.logger.log('A magical surge was chosen from NLoRME v1.2.')
               surge=random.choice(lines)
               file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/sparkles.png'), filename='sparkles.png')
               embed = discord.Embed(color=0x019cd0)
               embed.set_thumbnail(url='attachment://sparkles.png')
               embed.set_author(name='Wild Magic')
               embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                self.bot.logger.log(f'{e}')

        elif select == '2':
            try:
                lines = open(os.path.join(os.path.dirname(__file__), 'wildmagic/randommagicaleffects2.0.txt')).read().splitlines()
                self.bot.logger.log('A magical surge was chosen NLoRME v2.0.')
                surge=random.choice(lines)
                file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/sparkles.png'), filename='sparkles.png')
                embed = discord.Embed(color=0x019cd0)
                embed.set_thumbnail(url='attachment://sparkles.png')
                embed.set_author(name='Wild Magic')
                embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                self.bot.logger.log(f'{e}')

        elif select == '?':
            self.bot.logger.log(f'{ctx.message.author} asked for help with {self.prefix}wildmagic command.')
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Wild Magic)', icon_url='attachment://warning.png')
            embed.add_field(name='__WildMagic__', value=f'**Usage: `{self.prefix}wildmagic #`\n other aliases `{self.prefix}wm, {self.prefix}surge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!', inline=False)

        else:
            self.bot.logger.log(f'Invalid input for {self.prefix}wildmagic command.')
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Wild Magic', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f'That is not a valid input. Please try again or use `{self.prefix}wildmagic ?` for more information.', inline=False)


        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(WildMagic(bot))
