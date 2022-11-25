from base64 import b16decode
from operator import itemgetter
import os
import discord
from services.logService import LogService
from discord.ext import commands



# ---------------------------------------------------------
# Assistance
# ---------------------------------------------------------
class Help (commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.log(f'Feeling helpful.')


    async def cog_command_error(self, ctx, error):
        self.logger.error(f"error trying to run help: {error}")
        if isinstance(error, commands.CommandError):
            await ctx.send('Something went wrong. Try `!reload help`.')


    # ---------------------------------------------------------
    # Commands Listing
    # ---------------------------------------------------------
    @commands.command(aliases=['cmds','commands'])
    async def _cmds(self, ctx):
        def get_commands():
            x = []
            for y in self.bot.commands:
                x.append(f"**{y.name}** - " + f", ".join(y.aliases))
            return x

        x = get_commands()
        cmd_list = [c.replace("_","") for c in x]

        if commands.is_owner() or (ctx.author==ctx.guild.owner or ctx.author.has_permissions(administrator=True)):

            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name=f'Available Commands', icon_url='attachment://warning.png')
            embed.add_field(name=f'**__Commands__**', value="Below is a list of the individual commands available and all aliases that can be used to activate a given command.\n\n" + "\n".join(cmd_list), inline=False)
            print("Displayed all commands available to Administrators or Server Owners.")

        else:
            cmd_list.remove('reload','load','unload','servers','shutdown')
            icon = discord.File(os.path.join(os.path.dirname(__file__) + '/../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name=f'Available Commands', icon_url='attachment://warning.png')
            embed.add_field(name=f'**__Commands__**', value=f"\n".join(cmd_list), inline=False)
            print("Displayed all commands available to Users.")

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=icon, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=icon, embed=embed)


    # ---------------------------------------------------------
    # Help Command
    # ---------------------------------------------------------
    @commands.command()
    async def help(self, ctx, select):
        def get_help():
            help_list=[]
            x=[]
            entry=[]
            for y in self.bot.commands:
                x.append([y.name, y.aliases, y.extras])

            if len(x) != 0:
                for a in range(len(x)):
                    for b in range(len(x[a])):
                        if select.lower() in x[a][b]:
                            entry = x[a][b+1]
                        else:
                            for c in range(len(x[a][b])):
                                if select.lower() in x[a][b][c]:
                                    entry = x[a][b]
            else:
                entry=['**__Input Error__**', 'No such command exists. Try `!commands` for a full list of commands.', 'False']
            return(entry)

        help_list = get_help()

        icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
        embed = discord.Embed(color=0x019cd0)
        embed.set_author(name=f'Command Help', icon_url='attachment://warning.png')
        embed.add_field(name=help_list[0], value=help_list[1], inline=False)

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=icon, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=icon, embed=embed)

        #if commands.is_owner() or (ctx.author==ctx.guild.owner or ctx.author.has_permissions(administrator=True)):
        #    icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
        #    embed = discord.Embed(color=0x019cd0)
        #    embed.set_author(name=f'All Command Help', icon_url='attachment://prohibited.png')
        #    embed.add_field(name=f':dollar:  **__Loot__**', value=f'**Usage: `{self.prefix}loot #` where `# = 1-4`**\n Number corresponds to the 4 Individual Treasure tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins randomly based on table selected.\n", inline=False)
        #    embed.add_field(name=f':moneybag:  **__Hoard__**', value=f'**Usage: `{self.prefix}hoard #` where `# = 1-4`**\n Number corresponds to the 4 Treasure Hoard tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins and magical items randomly based on table selected.\n', inline=False)
        #    embed.add_field(name=f':gem:  **__Gems__**', value=f'**Usage: `{self.prefix}gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`n = number of gems to be generated`**\n Number corresponds to the 4 Individual Treasure tables in DMG - Chapter 7.\nThis will generate all coins randomly based on table selected.\n', inline=False)
        #    embed.add_field(name=f':ring:  **__Trinket__**', value=f'**Usage: `{self.prefix}trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.\n', inline=False)
        #    embed.add_field(name=f':sparkles:  **__WildMagic__**', value=f'**Usage: `{self.prefix}wildmagic #`\n other aliases `{self.prefix}wm, {self.prefix}surge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!\n', inline=False)
        #    embed.add_field(name=f':mag:  **__Collect__**', value=f'**Usage: `{self.prefix}collect b `\n`{self.prefix}search` and `{self.prefix}find` can also be used\nwhere `b = biome`**\nValid biome selections are:\n arctic, desert, forest, grass, hills, mountain, swamp, underdark, water, and common(not a biome but a list of components that can be found in any biome).', inline=False)
        #    embed.add_field(name=f':mushroom:  **__Herb Info__**', value=f"**Usage: `{self.prefix}herb name` or `{self.prefix}hinfo name` \nwhere `name = full name of herb`**\nHerb name is one of the components from [Herbalism and Alchemy](https://drive.google.com/file/d/0B7CIGCMCtoETVmhDNEZMbUVweTg/view) homebrew supplement By [Dalagrath](https://www.reddit.com/r/dndnext/comments/3w1log/5e_herbalism_alchemy_v12_updates_fanmade/) .\n", inline=False)
        #    embed.add_field(name=f":crystal_ball:  **__Oracle__**", value=f"**Usage: `{self.prefix}oracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
        #    embed.add_field(name=f':alembic:  **__Potion__**', value=f'**Usage: `{self.prefix}potion c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.', inline=False)
        #    embed.add_field(name=f':test_tube:  **__Poison__**', value=f'**Usage: `{self.prefix}poison c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.', inline=False)
        #    embed.add_field(name=f':floppy_disk:  **__Load__**', value=f'**Usage: `{self.prefix}load extension`\nWhere `extension = loot, hoard, roll`**\nWill load one of the listed command extensions following the use of the Unload command.\n', inline=False)
        #    embed.add_field(name=f':stop_sign:  **__Unload__**', value=f'**Usage: `{self.prefix}unload extension`\nWhere `extension = loot, hoard, roll`**\nWill unload one of the listed command extensions. Generally only used when extension becomes unresponsive with no error messages.\n', inline=False)
        #    embed.add_field(name=f':repeat:  **__Reload__**', value=f'**Usage: `{self.prefix}reload extension`\nWhere `extension = loot, hoard, roll`**\nWill perform Unload and Load functions together.\n', inline=False)
        #    embed.add_field(name=f':octagonal_sign: **__Shutdown__**', value=f'Terminates bot all bot functions. Need to be bot owner to use. Contact Eyeofthenyte#0042 with any issues.', inline=False)
        #    embed.add_field(name=f':wave:  **__Leave__**', value=f'**Usage: `{self.prefix}leave server`\nWhere `server = name of server`**\nWill make the bot leave the server.\n**Must be server owner to use this command.**\n', inline=False)
        #    embed.add_field(name=f':computer: **__Servers__**', value=f'A listing of servers the bot is curretntly connected to. Need to be bot owner to use. Contact Eyeofthenyte#0042 with any issues.', inline=False)
        #    print("Displayed Help for  Administrators or Server Owners.")

        #else:
        #    icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
        #    embed = discord.Embed(color=0x019cd0)
        #    embed.set_author(name=f'All Command Help', icon_url='attachment://prohibited.png')
        #    embed.add_field(name=f':dollar:  **__Loot__**', value=f"**Usage: `{self.prefix}loot #` where `# = 1-4`**\n Number corresponds to the 4 Individual Treasure tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins randomly based on table selected.\n", inline=False)
        #    embed.add_field(name=f':moneybag:  **__Hoard__**', value=f"**Usage: `{self.prefix}hoard #` where `# = 1-4`**\n Number corresponds to the 4 Treasure Hoard tables in Dungeon Master's Guide - Chapter 7.\nThis will generate all coins and magical items randomly based on table selected.\n", inline=False)
        #    embed.add_field(name=f':gem:  **__Gems__**', value=f'**Usage: `{self.prefix}gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`n = number of gems to be generated`**\n Number corresponds to the 4 Individual Treasure tables in DMG - Chapter 7.\nThis will generate all coins randomly based on table selected.\n', inline=False)
        #    embed.add_field(name=f':ring:  **__Trinket__**', value=f"**Usage: `{self.prefix}trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.\n", inline=False)
        #    embed.add_field(name=f':sparkles:  **__WildMagic__**', value=f'**Usage: `{self.prefix}wildmagic #`\n other aliases `{self.prefix}wm, {self.prefix}surge` will also work\nwhere `# = 1` for Net Libram of Magical Efects v1.2 (edited) \nwhere `# = 2` for Net Libram of Magical Efects v2.0**\n Takes random selection of one of the magic effects selections. Good luck!\n', inline=False)
        #    embed.add_field(name=f':mag:  **__Collect__**', value=f"**Usage: `{self.prefix}collect b `\n`{self.prefix}search` and `{self.prefix}find` can also be used\nwhere `b = biome`**\nValid biome selections are:\n arctic, desert, forest, grass, hills, mountain, swamp, underdark, water, and common(not a biome but a list of components that can be found in any biome).", inline=False)
        #    embed.add_field(name=f':mushroom:  **__Herb Info__**', value=f"**Usage: `{self.prefix}herb name` or `{self.prefix}hinfo name` \nwhere `name = full name of herb`**\nHerb name is one of the components from [Herbalism and Alchemy](https://drive.google.com/file/d/0B7CIGCMCtoETVmhDNEZMbUVweTg/view) homebrew supplement By [Dalagrath](https://www.reddit.com/r/dndnext/comments/3w1log/5e_herbalism_alchemy_v12_updates_fanmade/) .\n", inline=False)
        #    embed.add_field(name=f":crystal_ball:  **__Oracle__**", value=f"**Usage: `{self.prefix}oracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
        #    embed.add_field(name=f':alembic:  **__Potion__**', value=f"**Usage: `{self.prefix}potion c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)
        #    embed.add_field(name=f':test_tube:  **__Poison__**', value=f"**Usage: `{self.prefix}poison c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)
        #    print("Displayed all commands available to Users.")


async def setup(bot):
    await bot.add_cog(Help(bot))
