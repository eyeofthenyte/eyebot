import discord
import random
import os
import logging
from services.logService import LogService
from discord.ext import commands


def generate_individual_loot(select, d100_roll=None, randrange=None):
    """Generate one deterministic individual-treasure result."""
    if select not in {"1", "2", "3", "4"}:
        raise ValueError("Loot table must be between 1 and 4.")

    roll = randrange or random.randrange
    d100_roll = d100_roll if d100_roll is not None else roll(1, 101)
    if not 1 <= d100_roll <= 100:
        raise ValueError("d100 roll must be between 1 and 100.")

    coins = []
    if select == "1":
        challenge = "Challange 0 - 4"
        if d100_roll <= 30:
            coins.append(f"{roll(6, 31)} CP")
        elif d100_roll <= 60:
            coins.append(f"{roll(4, 25)} SP")
        elif d100_roll <= 70:
            coins.append(f"{roll(3, 19)} EP")
        elif d100_roll <= 95:
            coins.append(f"{roll(3, 19)} GP")
        else:
            coins.append(f"{roll(1, 7)} PP")
    elif select == "2":
        challenge = "Challange 5 - 10"
        if d100_roll <= 30:
            coins.extend((f"{roll(4, 24) * 100} CP", f"{roll(1, 6) * 10} EP"))
        elif d100_roll <= 60:
            coins.extend((f"{roll(6, 36) * 10} SP", f"{roll(2, 12) * 10} GP"))
        elif d100_roll <= 70:
            coins.extend((f"{roll(3, 18) * 10} EP", f"{roll(2, 12) * 10} GP"))
        elif d100_roll <= 95:
            coins.append(f"{roll(4, 24) * 10} GP")
        else:
            coins.extend((f"{roll(2, 12) * 10} GP", f"{roll(3, 18)} PP"))
    elif select == "3":
        challenge = "Challange 11 - 16"
        if d100_roll <= 20:
            coins.extend((f"{roll(4, 24) * 100} SP", f"{roll(1, 6) * 100} GP"))
        elif d100_roll <= 35:
            coins.extend((f"{roll(1, 6) * 100} EP", f"{roll(1, 6) * 100} GP"))
        elif d100_roll <= 75:
            coins.extend((f"{roll(2, 12) * 100} GP", f"{roll(1, 6) * 10} PP"))
        else:
            coins.extend((f"{roll(2, 12) * 100} GP", f"{roll(2, 12) * 10} PP"))
    else:
        challenge = "Challange 17+"
        if d100_roll <= 15:
            coins.extend((f"{roll(2, 12) * 1000} EP", f"{roll(8, 48) * 100} GP"))
        elif d100_roll <= 55:
            coins.extend((f"{roll(1, 6) * 1000} GP", f"{roll(1, 6) * 100} PP"))
        else:
            coins.extend((f"{roll(1, 6) * 1000} GP", f"{roll(2, 12) * 100} PP"))

    punctuation = "." if select == "1" else ""
    response = "At the end of your job you find...\n" + "\n".join(coins) + punctuation
    return {
        "challenge": challenge,
        "coins": tuple(coins),
        "d100_roll": d100_roll,
        "response": response,
    }


# ---------------------------------------------------------
# Random Loot Generator
# ---------------------------------------------------------
class Loot(commands.Cog):

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
        self.bot.logger.log(f"Looking for loose change.")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'missing or invalid argument for .loot')
            m_Response = "That's not a valid input. Please try again or `!help loot` for more information."
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Indivdual Treasure', icon_url='attachment://prohibited.png')
            embed.add_field(name='**__Error__**', value=f'{m_Response}', inline=False)

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=icon, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=icon, embed=embed)


    #----------------------------
    # Loot Command
    #----------------------------
    @commands.command(extras=[":dollar:  **__Loot__**", "**Usage: `!loot #` where `# = 1-4`**\n Number corresponds to the 4 Individual Treasure tables in DMG - Chapter 7.\nThis will generate all coins randomly based on table selected.\n"])
    async def loot(self, ctx, *, select):
        try:
            result = generate_individual_loot(select)
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/coin.png'), filename='coin.png')
            embed = discord.Embed(color=0xffe449)
            embed.set_author(name='Indivdual Treasure', icon_url='attachment://coin.png')
            embed.add_field(
                name=f"**__{result['challenge']}__**",
                value=result["response"],
                inline=False,
            )
        except ValueError:
            self.bot.logger.log(f'{ctx.message.author} entered invalid hoard opterator')
            m_Response = "That's not a valid input. Please try again or `!help loot` for more information."
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Indivdual Treasure', icon_url='attachment://prohibited.png')
            embed.add_field(name='**__Error__**', value=f'{m_Response}', inline=False)

        if discord.ChannelType == "private":
            self.bot.logger.log(f'{ctx.message.author} rolled for loot from table {select}.')
            await ctx.message.author.send(file=icon, embed=embed)
        elif discord.ChannelType != "private":
            self.bot.logger.log(f'{ctx.message.author} rolled for loot from table {select}.')
            await ctx.send(file=icon, embed=embed)

async def setup(bot):
    await bot.add_cog(Loot(bot))
