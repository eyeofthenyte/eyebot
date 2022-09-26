import sys, discord
import os, json, datetime, codecs, re
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find
from eyebot import t



# ---------------------------------------------------------
# Help Embed
# ---------------------------------------------------------
class Help (commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Feeling helpful.')
   
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send('Something went wrong. Try `.reload help`.')

        

    @commands.command(aliases=['h', 'help'])
    async def _help(self, ctx):
        embed = discord.Embed(color=0x019cd0)
        embed.set_author(name='Help (All Commands)')
        embed.add_field(name=':dollar:  **__Loot__**', value="**Usage: `.loot #` where `# = 1-4`**\n Number corresponds to the 4 Individual Treasure tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins randomly based on table selected.\n", inline=False)
        embed.add_field(name=':moneybag:  **__Hoard__**', value="**Usage: `.hoard #` where `# = 1-4`**\n Number corresponds to the 4 Treasure Hoard tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins and magical items randomly based on table selected.\n", inline=False)
        #embed.add_field(name=':floppy_disk:  **__Load__**', value='**Usage: `.load extension`\nWhere `extension = loot, hoard, roll`**\nWill load one of the listed command extensions following the use of the Unload command.\n', inline=False)
        #embed.add_field(name=':stop_sign:  **__Unload__**', value='**Usage: `.unload extension`\nWhere `extension = loot, hoard, roll`**\nWill unload one of the listed command extensions. Generally only used when extension becomes unresponsive with no error messages.\n', inline=False)
        #embed.add_field(name=':repeat:  **__Reload__**', value='**Usage: `.reload extension`\nWhere `extension = loot, hoard, roll`**\nWill perform Unload and Load functions together.\n', inline=False)
        #embed.add_field(name=':wave:  **__Leave__**', value='**Usage: `.leave server`\nWhere `server = name of server`**\nWill make the bot leave the server.\n**Must be server owner to use this command.**\n', inline=False)
        embed.add_field(name=':gem:  **__Gems__**', value='**Usage: `.gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`n = number of gems to be generated`**\n Number corresponds to the 4 Individual Treasure tables in DMG - Chapter 7.\nThis will generate all coins randomly based on table selected.\n', inline=False)
        embed.add_field(name=':ring:  **__Trinket__**', value="**Usage: `.trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.\n", inline=False)
        embed.add_field(name=':sparkles:  **__WildMagic__**', value='**Usage: `.wildmagic #`\n other aliases `.wm, .surge, .magicsurge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!\n', inline=False)
        embed.add_field(name=':mag:  **__Collect__**', value="**Usage: `.collect b `\n`.search` and `.find` can also be used\nwhere `b = biome`**\nValid biome selections are:\n arctic, desert, forest, grass, hills, mountain, swamp, underdark, water, and common(not a biome but a list of components that can be found in any biome).", inline=False)
        embed.add_field(name=':mushroom:  **__Herb Info__**', value="**Usage: `.herb name` or `.hinfo name` \nwhere `name = full name of herb`**\nHerb name is one of the components from [Herbalism and Alchemy](https://drive.google.com/file/d/0B7CIGCMCtoETVmhDNEZMbUVweTg/view) homebrew supplement By [Dalagrath](https://www.reddit.com/r/dndnext/comments/3w1log/5e_herbalism_alchemy_v12_updates_fanmade/) .\n", inline=False)
        embed.add_field(name=f":crystal_ball:  **__Oracle__**", value=f"**Usage: `.oracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
        embed.add_field(name=f':alembic:  **__Potion__**', value="**Usage: `.potion c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `.herb list` for a list of components or `.herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)
        embed.add_field(name=f':test_tube:  **__Poison__**', value="**Usage: `.poison c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `.herb list` for a list of components or `.herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)


        await ctx.message.delete()
        await ctx.message.author.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))