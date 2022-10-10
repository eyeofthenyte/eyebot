import eyebot_discord
import os, datetime
from discord.ext import commands

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

#Time Stamp Generation For Console Logging
def get_prefix():
    data = open(os.path.join(os.path.dirname(__file__), "../eyebot.cfg")).read().splitlines()
    prefix = data[1]
    return prefix
    data.close()

prefix = get_prefix()

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
        file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
        embed = discord.Embed(color=0x019cd0)
        embed.set_author(name=f'Help (All Commands)', icon_url='attachment://prohibited.png')
        embed.add_field(name=f':dollar:  **__Loot__**', value=f"**Usage: `{prefix}loot #` where `# = 1-4`**\n Number corresponds to the 4 Individual Treasure tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins randomly based on table selected.\n", inline=False)
        embed.add_field(name=f':moneybag:  **__Hoard__**', value=f"**Usage: `{prefix}hoard #` where `# = 1-4`**\n Number corresponds to the 4 Treasure Hoard tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins and magical items randomly based on table selected.\n", inline=False)
        embed.add_field(name=f':gem:  **__Gems__**', value=f'**Usage: `{prefix}gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`n = number of gems to be generated`**\n Number corresponds to the 4 Individual Treasure tables in DMG - Chapter 7.\nThis will generate all coins randomly based on table selected.\n', inline=False)
        embed.add_field(name=f':ring:  **__Trinket__**', value=f"**Usage: `{prefix}trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.\n", inline=False)
        embed.add_field(name=f':sparkles:  **__WildMagic__**', value=f'**Usage: `{prefix}wildmagic #`\n other aliases `{prefix}wm, {prefix}surge, {prefix}magicsurge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!\n', inline=False)
        embed.add_field(name=f':mag:  **__Collect__**', value=f"**Usage: `{prefix}collect b `\n`{prefix}search` and `{prefix}find` can also be used\nwhere `b = biome`**\nValid biome selections are:\n arctic, desert, forest, grass, hills, mountain, swamp, underdark, water, and common(not a biome but a list of components that can be found in any biome).", inline=False)
        embed.add_field(name=f':mushroom:  **__Herb Info__**', value=f"**Usage: `{prefix}herb name` or `{prefix}hinfo name` \nwhere `name = full name of herb`**\nHerb name is one of the components from [Herbalism and Alchemy](https://drive.google.com/file/d/0B7CIGCMCtoETVmhDNEZMbUVweTg/view) homebrew supplement By [Dalagrath](https://www.reddit.com/r/dndnext/comments/3w1log/5e_herbalism_alchemy_v12_updates_fanmade/) .\n", inline=False)
        embed.add_field(name=f":crystal_ball:  **__Oracle__**", value=f"**Usage: `{prefix}oracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
        embed.add_field(name=f':alembic:  **__Potion__**', value=f"**Usage: `{prefix}potion c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{prefix}herb list` for a list of components or `{prefix}herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)
        embed.add_field(name=f':test_tube:  **__Poison__**', value=f"**Usage: `{prefix}poison c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{prefix}herb list` for a list of components or `{prefix}herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)
        #embed.add_field(name=f':floppy_disk:  **__Load__**', value=f'**Usage: `{prefix}load extension`\nWhere `extension = loot, hoard, roll`**\nWill load one of the listed command extensions following the use of the Unload command.\n', inline=False)
        #embed.add_field(name=f':stop_sign:  **__Unload__**', value=f'**Usage: `{prefix}unload extension`\nWhere `extension = loot, hoard, roll`**\nWill unload one of the listed command extensions. Generally only used when extension becomes unresponsive with no error messages.\n', inline=False)
        #embed.add_field(name=f':repeat:  **__Reload__**', value=f'**Usage: `{prefix}reload extension`\nWhere `extension = loot, hoard, roll`**\nWill perform Unload and Load functions together.\n', inline=False)
        #embed.add_field(name=f':wave:  **__Leave__**', value=f'**Usage: `{prefix}leave server`\nWhere `server = name of server`**\nWill make the bot leave the server.\n**Must be server owner to use this command.**\n', inline=False)


        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
