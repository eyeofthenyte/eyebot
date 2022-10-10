import eyebot_discord
import os, datetime
import random
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
               file = discord.File('./eyebot/images/commands/sparkles.png', filename='sparkles.png')
               embed = discord.Embed(color=0x019cd0)
               embed.set_thumbnail(url='attachment://sparkles.png')
               embed.set_author(name='Wild Magic')
               embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                print(f'{t()}: {e}')

        elif select == '2':
            try:
                lines = open(os.path.join(os.path.dirname(__file__), './wildmagic/randommagicaleffects2.0.txt')).read().splitlines()
                print('A magical surge was chosen LoRME v2.0.')
                surge=random.choice(lines)
                file = discord.File('./eyebot/images/commands/sparkles.png', filename='sparkles.png')
                embed = discord.Embed(color=0x019cd0)
                embed.set_thumbnail(url='attachment://sparkles.png')
                embed.set_author(name='Wild Magic')
                embed.add_field(name='__Effect__', value=f'{surge}', inline=False)
            except Exception as e:
                print(f'{t()}: {e}')

        elif select == '?':
            print(f'{t()}: {ctx.message.author} asked for help with {prefix}wildmagic command.')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Wild Magic)', icon_url='attachment://warning.png')
            embed.add_field(name='__WildMagic__', value=f'**Usage: `{prefix}wildmagic #`\n other aliases `{prefix}wm, {prefix}surge, {prefix}magicsurge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!', inline=False)

        else:
            print(f'{t()}: Invalid input for {prefix}wildmagic command.')
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Wild Magic', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f'That is not a valid input. Please try again or use `{prefix}wildmagic ?` for more information.', inline=False)


        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

def setup(bot):
    bot.add_cog(WildMagic(bot))
