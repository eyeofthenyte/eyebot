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
    @commands.command(aliases=['wildmagic', 'wm', 'surge'], extras=[":sparkles:  **__WildMagic__**", "**Usage:** `!wildmagic #`\n other aliases `!wm, !surge` will also work\n**where** `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0\n Takes random selection of one of the magic effects selections. Good luck!\n"])
    async def _wildmagic(self, ctx, *, select):

        if select == '1':
            try:
               lines = open(os.path.join(os.path.dirname(__file__), 'wildmagic/randommagicaleffects2.0.txt')).read().splitlines()
               self.bot.logger.log('A magical surge was chosen from NLoRME v1.2.')
               surge=random.choice(lines)
               icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/sparkles.png'), filename='sparkles.png')
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
                icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/sparkles.png'), filename='sparkles.png')
                embed = discord.Embed(color=0x019cd0)
                embed.set_thumbnail(url='attachment://sparkles.png')
                embed.set_author(name='Wild Magic')
                embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                self.bot.logger.log(f'{e}')

        else:
            self.bot.logger.log(f'Invalid input for !wildmagic command.')
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Wild Magic', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f'That is not a valid input. Please try again or use `!help wildmagic` for more information.', inline=False)


        if discord.ChannelType == "private":
            await ctx.message.author.send(file=icon, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=icon, embed=embed)

async def setup(bot):
    await bot.add_cog(WildMagic(bot))
