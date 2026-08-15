import os
import discord
import random
from services.googleSheetsService import (
    GoogleSheetsError,
    get_google_sheets_service,
    refresh_command,
)
from discord.ext import commands

TRINKET_SHEET_KEY = '1dwpn9CbEtwlkfzH4Qh0KafwZ2kvWarrDJCqPuR3fe0Q'

# =====================
# Trinket Cog Definition
# =====================
class Trinket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]
        self.sheets = get_google_sheets_service(bot)
        self.sheets.register_workbook(TRINKET_SHEET_KEY)

    async def cog_load(self):
        try:
            await self.sheets.worksheets(TRINKET_SHEET_KEY)
        except GoogleSheetsError as error:
            self.logger.warning(f"Unable to warm Trinket data: {error}")

    # Log when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Staring at the shinies.')

    # Error handler for command errors specific to this cog
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'{ctx.message.author} is missing or invalid argument for !trinket')
            try:
                sheet_data = await self.get_trinket_data()
            except GoogleSheetsError:
                sheet_data = {}
            error_m = 'Please select one of the following classes:\n' + \
                      ", ".join(sheet_data.keys()) + \
                      '.\nType `!trinket ?` for more info.'
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Trinket', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=error_m, inline=False)

            # Send to DM or channel depending on context
            if isinstance(ctx.channel, discord.DMChannel):
                await ctx.message.author.send(file=icon, embed=embed)
            else:
                await ctx.send(file=icon, embed=embed)

    # Lookup trinket list by class name
    async def get_trinket_data(self, select: str | None = None):
        worksheets = await self.sheets.worksheets(TRINKET_SHEET_KEY)
        sheet_data = {
            worksheet.title.lower(): [
                value for value in worksheet.col_values(2) if value
            ]
            for worksheet in worksheets
        }
        if select is None:
            return sheet_data
        key = select.lower()
        return key, sheet_data.get(key)

    # Build an embed for a valid trinket draw
    def build_trinket_embed(self, class_key: str, trinkets: list):
        image_path = os.path.join(os.path.dirname(__file__), f'../../images/classes/{class_key}.jpeg')
        icon_file = discord.File(image_path, filename=f'{class_key}.jpeg')

        embed = discord.Embed(color=0x019cd0)
        embed.set_thumbnail(url=f'attachment://{class_key}.jpeg')
        embed.set_author(name=f'{class_key.upper()} TRINKET')
        embed.add_field(name='You found the following:', value=random.choice(trinkets), inline=False)

        return embed, icon_file

    # Build an error embed if an invalid class was given
    def build_error_embed(self):
        icon_file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'),
                                 filename='prohibited.png')
        embed = discord.Embed(color=0xcc0000)
        embed.set_author(name='Trinket', icon_url='attachment://prohibited.png')
        embed.add_field(
            name='__Error__',
            value="That was not a valid choice. Please select an available Character Class. Type `!help trinket` for more info.",
            inline=False
        )
        return embed, icon_file

    # ========== Main Command ==========
    @commands.command()
    async def trinket(self, ctx, *, select):
        """
        Returns a random trinket based on the selected Dungeons & Dragons character class.
        Each class corresponds to a specific trinket table sourced from Nerd Immersion.

        Usage:
        `!trinket <class>`

        Examples:
        `!trinket bard` - Returns a Bard-themed trinket
        `!trinket rogue` - Returns a Rogue-themed trinket
        `!trinket refresh` - Administrators and stream moderators reload the cache

        """

        if select.strip().casefold() == "refresh":
            await refresh_command(ctx, self.sheets, TRINKET_SHEET_KEY, "Trinket")
            return

        try:
            class_key, trinkets = await self.get_trinket_data(select)
        except GoogleSheetsError as error:
            self.bot.logger.error(f'Trinket data unavailable: {error}')
            await ctx.send("❌ Trinket data is temporarily unavailable.")
            return

        if trinkets:
            embed, icon = self.build_trinket_embed(class_key, trinkets)
            self.bot.logger.log(f'{ctx.message.author} drew a random trinket from the {class_key.upper()} list.')
        else:
            embed, icon = self.build_error_embed()
            self.bot.logger.log('Invalid input for !trinket command.')

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.message.author.send(file=icon, embed=embed)
        else:
            await ctx.send(file=icon, embed=embed)

# Entry point to register the cog
async def setup(bot):
    await bot.add_cog(Trinket(bot))
