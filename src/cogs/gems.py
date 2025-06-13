import discord
import re
import os
import random
from services.logService import LogService
from discord.ext import commands

# ---------------------------------------------------------
# Gems Cog: Random gem generator for treasure/loot systems
# ---------------------------------------------------------
class Gems(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]

    # ----------------------------
    # Event: on_ready
    # ----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log('Staring at the shinies.')

    # ----------------------------
    # Error Handler for Gems Command
    # ----------------------------
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log('Missing or invalid argument for gems command.')

            # Prepare error embed
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='RANDOM GEM SELECTION', icon_url='attachment://prohibited.png')
            embed.add_field(
                name="**__Error__**",
                value="That's not a valid input. Please try again or use `!help gems` for more information.",
                inline=False
            )

            # Send the embed to the appropriate channel
            if isinstance(ctx.channel, discord.DMChannel):
                await ctx.message.author.send(file=icon, embed=embed)
            else:
                await ctx.send(file=icon, embed=embed)

    # ----------------------------
    # Command: !gems <value> <amount>
    # ----------------------------
    @commands.command()
    async def gems(self, ctx, *, gemstring):
        """
        💎 Generate random gems based on value and quantity.

        Usage:
        ------
        `!gems <value> <amount>`

        Parameters:
        -----------
        value : int
            The gp (gold piece) value of the gems you want to generate.
            Must match a file in the `./gems/` folder, e.g., `10gp.txt`, `50gp.txt`.

        amount : int
            The number of random gems to generate (1–50).

        Description:
        ------------
        Randomly selects gems from the corresponding value tier file and sends a 
        list of results in an embed. Each gem entry in the file should be formatted:
        `GemName;Description`

        Example:
        --------
        !gems 50 3
        → Picks 3 gems from `50gp.txt`

        Output:
        -------
        - Sends an embed with a list of randomly chosen gems (name + description)
        - If invalid input is provided, a helpful error message is shown.

        Files Required:
        ---------------
        - Folder: ./gems/
        - Files: [10gp.txt, 50gp.txt, 100gp.txt, etc.]
          Each line must be formatted as: Name;Description
        """

        gems = []

        # Check for proper input format (must have space)
        if not re.search(r"\s", gemstring):
            await self.send_error_embed(ctx, "Invalid format. Use `!gems <value> <amount>` (e.g., `!gems 50 3`).")
            return

        gem_parts = gemstring.strip().split()

        if len(gem_parts) != 2:
            await self.send_error_embed(ctx, "Invalid number of arguments. Use `!gems <value> <amount>`.")
            return

        gp_value, count = gem_parts

        # Validate that count is a positive integer
        try:
            count = int(count)
            if count < 1 or count > 50:
                raise ValueError
        except ValueError:
            await self.send_error_embed(ctx, "Amount must be a number between 1 and 50.")
            return

        # Construct path to gem table
        filepath = os.path.join(os.path.dirname(__file__), f'./gems/{gp_value}gp.txt')

        if not os.path.isfile(filepath):
            await self.send_error_embed(ctx, f"No gem table found for `{gp_value}gp`. Please check available tiers.")
            return

        # Read and randomly select gems
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.read().splitlines()

            for _ in range(count):
                randline = random.choice(lines)
                name, description = randline.split(";")
                gems.append(f"- {name.strip()}: {description.strip()}")

        except Exception as e:
            self.bot.logger.log(f"Error reading gem file: {e}")
            await self.send_error_embed(ctx, "There was a problem generating your gems. Please try again.")
            return

        # Log success
        self.bot.logger.log(f"{ctx.message.author} found {count} x {gp_value}gp gems.")

        # Create result embed
        icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/gem-stone.png'), filename='gem-stone.png')
        embed = discord.Embed(color=0x019cd0)
        embed.set_thumbnail(url='attachment://gem-stone.png')
        embed.set_author(name='RANDOM GEM SELECTION')
        embed.add_field(name=f'You discovered the following {gp_value}gp gems:', value='\n'.join(gems), inline=False)

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.message.author.send(file=icon, embed=embed)
        else:
            await ctx.send(file=icon, embed=embed)

    # ----------------------------
    # Utility: Send formatted error embed
    # ----------------------------
    async def send_error_embed(self, ctx, message):
        icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
        embed = discord.Embed(color=0x019cd0)
        embed.set_author(name='GEMS - ERROR', icon_url='attachment://prohibited.png')
        embed.add_field(name="**__Error__**", value=message, inline=False)

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.message.author.send(file=icon, embed=embed)
        else:
            await ctx.send(file=icon, embed=embed)

# ----------------------------
# Setup Function for Cog Loader
# ----------------------------
async def setup(bot):
    await bot.add_cog(Gems(bot))
