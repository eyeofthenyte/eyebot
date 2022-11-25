import discord
import os
import gspread
import random
from services.logService import LogService
from discord.ext import commands

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
        self.config = bot.config
        self.prefix = self.config["prefix"]

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Should be an interesting night.')

    async def cog_command_error(self, ctx, error):
        self.bot.logger.error(f'Carousing encountered error {error}')
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.error(f'{ctx.message.author} is missing or invalid argument for carousing')
            if discord.ChannelType == "private":
                await ctx.message.author.send(f'Please only type `!carousing` to get a random result.\n Type `!help carousing` for more info.')
                return
            else:
                await ctx.send(f'Please only type `!carousing` to get a random result.\n Type `!help carousing` for more info.')
                return

    #----------------------------
    # Carousing Command
    #----------------------------
    #----------------------------
    @commands.command(aliases=['carousing','carouse','drinking','getdrinks','pubcrawl'], extras=[":beers:  **__Carousing__**","**Usage: `!carousing`\nOther valid uses`!carouse`, `!drinking`, `!getdrinks` or `!pubcrawl`\n\nMakes a random selection from a table of possible drunken outcomes.\n"])
    async def _carousing(self, ctx):
        if ctx == ctx and gsa:
            self.bot.logger.info(f'A selection from the D100 Carousing list was made.')

            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/mugs.png'), filename='mugs.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url = 'attachment://mugs.png')
            embed.set_author(name = 'D100 CAROUSING TABLE')
            embed.add_field(name = 'You wake up... ', value = random.choice(c_list), inline=False)
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=icon, embed=embed)
            else:
                await ctx.send(file=icon, embed=embed)

        else:
            self.bot.logger.error(f'there was an error.')

            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Carousing', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Check `!help carousing` for more info.", inline=False)

            self.bot.logger.error(f'Invalid input for carousing command.')
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=icon, embed=embed)
            else:
                await ctx.send(file=icon, embed=embed)


async def setup(bot):
    await bot.add_cog(Carousing(bot))
