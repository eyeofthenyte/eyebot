import discord
import os
import random
from services.googleSheetsService import GoogleSheetsError, get_google_sheets_service
from discord.ext import commands

CAROUSING_SHEET_KEY = '1cezqq4iN5gToVHEVKcs8HgC8XFLsDe_7vX-KslL_Q30'

# ---------------------------------------------------------
# Random Carousing Outcome
# ---------------------------------------------------------
class Carousing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]
        self.sheets = get_google_sheets_service(bot)

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
        try:
            worksheet = await self.sheets.worksheet(CAROUSING_SHEET_KEY)
            outcomes = [value for value in worksheet.col_values(1) if value]
            if not outcomes:
                raise GoogleSheetsError("The carousing worksheet is empty.")

            self.bot.logger.info(f'A selection from the D100 Carousing list was made.')

            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/mugs.png'), filename='mugs.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url = 'attachment://mugs.png')
            embed.set_author(name = 'D100 CAROUSING TABLE')
            embed.add_field(name = 'You wake up... ', value = random.choice(outcomes), inline=False)
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=icon, embed=embed)
            else:
                await ctx.send(file=icon, embed=embed)

        except GoogleSheetsError as error:
            self.bot.logger.error(f'Carousing data unavailable: {error}')

            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Carousing', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value="Carousing data is temporarily unavailable.", inline=False)

            if discord.ChannelType == "private":
                await ctx.message.author.send(file=icon, embed=embed)
            else:
                await ctx.send(file=icon, embed=embed)


async def setup(bot):
    await bot.add_cog(Carousing(bot))
