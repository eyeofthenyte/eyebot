import os
import discord
import gspread
import random
from services.logService import LogService
from discord.ext import commands

# =====================
# Load Google Sheets and cache worksheet data
# =====================
GSA = None
SHEET_DATA = {}

# Define the path to the Google service account credentials
sheet_file_path = os.path.join(os.path.dirname(__file__), '../../service_account.json')
if os.path.exists(sheet_file_path):
    GSA = gspread.service_account(filename=sheet_file_path)
    sheet = GSA.open_by_key('1dwpn9CbEtwlkfzH4Qh0KafwZ2kvWarrDJCqPuR3fe0Q')
    worksheets = sheet.worksheets()
    for ws in worksheets:
        name = ws.title  # Sheet title assumed to be the class name
        values = list(filter(None, ws.col_values(2)))  # Get non-empty values from column B
        SHEET_DATA[name.lower()] = values  # Store by lowercase class name

# =====================
# Trinket Cog Definition
# =====================
class Trinket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]

    # Log when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Staring at the shinies.')

    # Error handler for command errors specific to this cog
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'{ctx.message.author} is missing or invalid argument for !trinket')
            error_m = 'Please select one of the following classes:\n' + \
                      ", ".join(SHEET_DATA.keys()) + \
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
    def get_trinket_data(self, select: str):
        key = select.lower()
        return key, SHEET_DATA.get(key)

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

        """

        class_key, trinkets = self.get_trinket_data(select)

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
