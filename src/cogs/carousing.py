import gspread
import random
import logging
from services.logService import LogService
from discord.ext import commands

from services.logService import LogService

gsa = 0
if os.path.exists(os.path.dirname(__file__) + '/../../service_account.json'):
    gsa = gspread.service_account(filename = os.path.dirname(__file__) + '/../../service_account.json')
    s = gsa.open_by_key('1cezqq4iN5gToVHEVKcs8HgC8XFLsDe_7vX-KslL_Q30')
    wks=s.get_worksheet(0)
    c_list = wks.col_values(1)

# ---------------------------------------------------------
# Random Carousing Outcome
# ---------------------------------------------------------
class Carousing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Should be an interesting night.')

    async def cog_command_error(self, ctx, error):
        self.bot.logger.error(f'Carousing encountered error {error}')
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.error(f'{ctx.message.author} is missing or invalid argument for .carousing')
            if discord.ChannelType == "private":
                await ctx.message.author.send(f'Please only type `{self.bot.config.get().prefix}carousing` to get a random result.\n Type `help` for more info.')
                return
            else:
                await ctx.send(f'Please only type `{self.bot.config.get().prefix}carousing` to get a random result.\n Type `help` for more info.')
                return

    #----------------------------
    # Carousing Command
    #----------------------------
    @commands.command(aliases=['carousing','carouse','drinking','getdrinks','pubcrawl'])
    async def _carousing(self, ctx):
        if ctx == ctx and gsa:
            self.bot.logger.info(f'A selection from the D100 Carousing list was made.')

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
            self.bot.logger.error(f'there was an error.')

            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Carousing', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Simply type `{self.bot.config.get().prefix}carousing`, `{self.bot.config.get().prefix}carouse`, `self.bot.config.get().prefixdrinking`, `self.bot.config.get().prefixgetdrinks`, or `self.bot.config.get().prefixpubcrawl` to get a selection from the table.", inline=False)

            self.bot.logger.error(f'Invalid input for carousing command.')
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=file, embed=embed)
            else:
                await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(Carousing(bot))
