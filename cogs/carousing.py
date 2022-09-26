import sys, discord, logging
import os, json, datetime, codecs, re, gspread
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

gsa = gspread.service_account(filename = 'eyebot/service_account.json')
s = gsa.open_by_key('1cezqq4iN5gToVHEVKcs8HgC8XFLsDe_7vX-KslL_Q30')
wks=s.get_worksheet(0)
c_list = wks.col_values(1)

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

class Carousing(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Should be an interesting night.')

    async def cog_command_error(self, ctx, error):
        print(f'Carousing encountered error {error}')
        if isinstance(error, commands.MissingRequiredArgument):
            print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) is missing or invalid argument for .carousing')
            await ctx.send(f'Please only type `.carousing` to get a random result.\n Type `.help` for more info.')
            return

    #----------------------------
    # Carousing Command
    #----------------------------
    @commands.command(aliases=['carousing','carouse','drinking','getdrinks','pubcrawl'])
    async def _carousing(self, ctx):
        if ctx == ctx:
            print(f'{t()}: A selection from the D100 Carousing list was made.')
            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/google/313/clinking-beer-mugs_1f37b.png')
            embed.set_author(name = 'D100 CAROUSING TABLE')
            embed.add_field(name = 'You wake up... ', value = random.choice(c_list), inline=False)
            await ctx.send(embed=embed)

        else: 
            print(f'{t()}: there was an error.')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Carousing', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Simply type `carousing`, `carouse`, `drinking`, `getdrinks`, or `pubcrawl` to get a selection from the table.", inline=False)     
            print(f'{t()}: Invalid input for carousing command.')
            await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(Carousing(bot))
