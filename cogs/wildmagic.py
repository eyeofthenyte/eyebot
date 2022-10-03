import sys, discord
import os, json, datetime, codecs, re
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find

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
# Loot Hoard Generator
# ---------------------------------------------------------
class WildMagic(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Magic is getting chaotic.')


    #----------------------------
    # Wild Magic Surge
    #----------------------------
    @commands.command(aliases=['wildmagic', 'wm', 'surge', 'magicsurge'])
    async def _wildmagic(self, ctx, *, select):

        if select == '1':
            try:
               lines = open(os.path.join(os.path.dirname(__file__), './wildmagic/randommagicaleffects2.0.txt')).read().splitlines()
               print('A magical surge was chosen from NLoRME v1.2.')
               surge=random.choice(lines)
               embed = discord.Embed(color=0x019cd0)
               embed.set_author(name='Wild Magic', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/sparkles_2728.png')
               embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                print(f'{t()}: {e}')

        elif select == '2':
            try:
                lines = open(os.path.join(os.path.dirname(__file__), './wildmagic/randommagicaleffects2.0.txt')).read().splitlines()
                print('A magical surge was chosen LoRME v2.0.')
                surge=random.choice(lines)
                embed = discord.Embed(color=0x019cd0)
                embed.set_author(name='Wild Magic', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/sparkles_2728.png')
                embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                print(f'{t()}: {e}')

        elif select == '?':
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Wild Magic)', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/warning_26a0.png')
            embed.add_field(name='__WildMagic__', value=f'**Usage: `{prefix}wildmagic #`\n other aliases `{prefix}wm, {prefix}surge, {prefix}magicsurge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!', inline=False)

        else:
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Wild Magic', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='__Error__', value=f'That is not a valid input. Please try again or use `.wildmagic ?` for more information.', inline=False)     
            print(f'{t()}: Invalid input for {prefix}wildmagic command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(WildMagic(bot))
