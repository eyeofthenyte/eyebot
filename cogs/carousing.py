import sys, eyebot_discord, logging
import os, datetime, gspread
import random
from discord.ext import commands


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

#Pass Bot Prefix
def get_prefix():
    data = open(os.path.join(os.path.dirname(__file__), "../eyebot.cfg")).read().splitlines()
    prefix = data[1]
    return prefix
    data.close()

prefix = get_prefix()

# ---------------------------------------------------------
# Random Carousing Outcome
# ---------------------------------------------------------
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
            print(f'{t()}: {ctx.message.author} is missing or invalid argument for .carousing')
            if discord.ChannelType == "private":
                await ctx.message.author.send(f'Please only type `{prefix}carousing` to get a random result.\n Type `help` for more info.')
                return
            else:
                await ctx.send(f'Please only type `{prefix}carousing` to get a random result.\n Type `help` for more info.')
                return

    #----------------------------
    # Carousing Command
    #----------------------------
    @commands.command(aliases=['carousing','carouse','drinking','getdrinks','pubcrawl'])
    async def _carousing(self, ctx):
        if ctx == ctx:
            print(f'{t()}: A selection from the D100 Carousing list was made.')
            file = discord.File('./eyebot/images/commands/mugs.png', filename='mugs.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url = 'attachment://mugs.png')
            embed.set_author(name = 'D100 CAROUSING TABLE')
            embed.add_field(name = 'You wake up... ', value = random.choice(c_list), inline=False)
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=file, embed=embed)
            else:
                await ctx.send(file=file, embed=embed)

        else:
            print(f'{t()}: there was an error.')
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Carousing', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Simply type `{prefix}carousing`, `{prefix}carouse`, `{prefix}drinking`, `{prefix}getdrinks`, or `{prefix}pubcrawl` to get a selection from the table.", inline=False)
            print(f'{t()}: Invalid input for carousing command.')
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=file, embed=embed)
            else:
                await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(Carousing(bot))
