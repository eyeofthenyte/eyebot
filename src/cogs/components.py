from copyreg import pickle
import discord
import os
import gspread
import random
from services.logService import LogService
from discord.ext import commands, tasks
from discord.utils import find
from gsheets import Sheets

gsa = 0

if os.path.exists(os.path.dirname(__file__) + '../../../service_account.json'):
    gsa = gspread.service_account(filename = os.path.dirname(__file__) + '../../../service_account.json')
    s = gsa.open_by_key('1wkaF--4DqTComUfX1dYbjhkRimR2raYbJm3IEa1CTq0')

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

# ---------------------------------------------------------
# Herbalism and Alchemey Commands
# ---------------------------------------------------------
class Components(commands.Cog):

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
        self.bot.logger.log(f'Looking for the special grass.')

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'missing or invalid argument for search or component')
            if discord.ChannelType == "private":
                await message.author.send(f'Please choose which region you wish to search in: arctic, common, desert, forest, grass, hills, mountain, swamp, underdark, and water.\nWater biome is used for coastal areas as well.')
                return
            elif discord.ChannelType != "private":
                await ctx.send(f'Please choose which region you wish to search in: arctic, common, desert, forest, grass, hills, mountain, swamp, underdark, and water.\nWater biome is used for coastal areas as well.')
                return

    #----------------------------
    # Collect Command
    #----------------------------
    @commands.command(aliases=['collect', 'search', 'find', 'gather'], extras=["f':mag:  **__Collect__**'", "f'**Usage: `{self.prefix}collect b `\n`{self.prefix}search` and `{self.prefix}find` can also be used\nwhere `b = biome`**\nValid biome selections are:\n arctic, desert, forest, grass, hills, mountain, swamp, underdark, water, and common(not a biome but a list of components that can be found in any biome).'", "inline=False"])
    async def _collect(self, ctx, *, select):

        pick = select
        biome = ['arctic','common','desert','forest','grass','hills','mountain','swamp','underdark','water']
        icon = ['snowflake','world-map','desert','deciduous-tree','seedling','sunrise-over-mountains','mountain','sheaf-of-rice','hole','water-wave']
        w = ["0", "1", "2", "8", "9", "10"]
        percentage = random.randrange(1,101)
        if pick.lower() in str(biome).lower():
             for i in range(len(biome)):
                if pick.lower() == biome[i].lower():
                    biomedoc = open(os.path.join(os.path.dirname(__file__), "components/" + pick.lower() + ".txt")).read().splitlines()
                    randline = random.choice(biomedoc)
                    list = randline.split(";")
                    component = list[0]
                    qty = 1
                    if component in w:
                        if (percentage > 75):
                            qty = str(random.randrange(1,5))
                            list[2] = " Elemental Water"
                    else:
                        if list[1] == '1':
                            qty = str(random.randrange(1,5))
                        elif list[1] == '2':
                            qty = str(random.randrange(1,9)*2)
                        else:
                            common = open(os.path.join(os.path.dirname(__file__), "components/common.txt")).read().splitlines()
                            randline = random.choice(common)
                            list = randline.split(";")
                            qty = str(random.randrange(1,5))

                    m_Response = str(qty) + "x " + list[2]
                    file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/'+icon[i]+'.png'))
                    self.bot.logger.log(f'Components from the ' + pick.upper() + ' biome were found.')
                    embed = discord.Embed(color=0x019cd0)
                    embed.set_author(name = pick.upper() + ' BIOME COMPONENTS', icon_url='attachment://'+icon[i]+'.png')
                    embed.add_field(name = 'You found the following alchemic components:', value = m_Response, inline=False)

        elif pick == '?':
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Collect)', icon_url='attachment://warning.png')
            embed.add_field(name='**__Collect__**', value=f"**Usage: `{self.prefix}collect b`\nwhere `b = biome`**\nValid biome selections are:\n arctic, desert, forest, grass, hills, mountain, swamp, underdark, water, and common(not a biome but a list of components that can be found in any biome)", inline=False)
            self.bot.logger.log(f'{ctx.message.author} asked for help with {self.prefix}collect.')

        else:
            self.bot.logger.log(f'there was an error.')

            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Collect', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select an available biome. Type `{self.prefix}collect ?` for more info.", inline=False)

            self.bot.logger.log(f'{ctx.message.author} gave an invalid input for collect command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

    #----------------------------
    # Info Command
    #----------------------------
    @commands.command(aliases=['herb', 'hinfo', 'flora'], extras=["f':mushroom:  **__Herb Info__**'", "f'**Usage: `{self.prefix}herb name` or `{self.prefix}hinfo name` \nwhere `name = full name of herb`**\nHerb name is one of the components from [Herbalism and Alchemy](https://drive.google.com/file/d/0B7CIGCMCtoETVmhDNEZMbUVweTg/view) homebrew supplement By [Dalagrath](https://www.reddit.com/r/dndnext/comments/3w1log/5e_herbalism_alchemy_v12_updates_fanmade/) .\n'", "inline=False"])
    async def _flora(self, ctx, *, select):
        if not gsa:
            return

        ws = s.worksheet("Ingredients")
        c_list = ws.col_values(1)
        rarity = ['Common (Up to 15 GP)','Uncommon (16-40 GP)','Rare (41-100 GP)','Very Rare (100-150 GP)']
        type = ['Potion','Poison','Enchantment','Potion & Poison']
        hr = '__'

        if select.lower() in str(c_list).lower():
            for i in range(len(c_list)):
                if select.lower() == c_list[i].lower():
                    biomeicons = str(ws.cell(i+1,6).value).replace('Arctic',':snowflake:').replace('Any',':world_map:').replace('Desert',':desert:').replace('Forest',':deciduous_tree:').replace('Grasslands',':seedling:').replace('Hills',':sunrise_over_mountains:').replace('Mountain',':mountain:').replace('Swamp',':ear_of_rice:').replace('Underdark',':hole:').replace('Coastal',':water_wave:')
                    self.bot.logger.log(f'The entry for ' + select.upper() + ' was requested.')
                    file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/open-book.png'), filename='open-book.png')
                    embed = discord.Embed(color=0x019cd0, title="ALCHEMIST'S JOURNAL")
                    embed.set_author(name = f'DESCRIPTION', icon_url='attachment://open-book.png')
                    embed.add_field(name = f'__*{select.upper()}*__     {biomeicons}', value=f'*{ws.cell(i+1,2).value}*', inline=False)
                    embed.add_field(name = f'Effect', value=f'*{ws.cell(i+1,3).value}*\n', inline=False)
                    embed.set_footer(text= f'Rarity: {rarity[int(ws.cell(i+1,4).value)]}  --  Ingredient Type: {type[int(ws.cell(i+1,5).value)]}')

        elif select == 'list':
            components = str(c_list).replace("'","").replace("[","").replace("]","").replace('"','')
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/open-book.png'), filename='open-book.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Table of Contents', icon_url='attachment://open-book.png')
            embed.add_field(name='**__Herbs__**', value=str(components).replace(',','\n'), inline=False)
            self.bot.logger.log(f'{ctx.message.author} looked at Herb Information table of contents.')

        elif select == '?':
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Herb Info)', icon_url='attachment://warning.png')
            embed.add_field(name='**__Herb Info__**', value=f"**Usage: `{self.prefix}hinfo name` \nwhere `name = full name of herb`**\nHerb name is one of the components from [Herbalism and Alchemy](https://drive.google.com/file/d/0B7CIGCMCtoETVmhDNEZMbUVweTg/view) homebrew supplement By [Dalagrath](https://www.reddit.com/r/dndnext/comments/3w1log/5e_herbalism_alchemy_v12_updates_fanmade/).\nTo get a list of components please use `{self.prefix}herb list` or `{self.prefix}herb (herb name)` to get a descripton of the component.", inline=False)
            self.bot.logger.log(f'{ctx.message.author} asked for help with Herb Information.')


        else:
            self.bot.logger.log(f'there was an error.')

            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Herb Info', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select a component that has an entry. Type `{self.prefix}herb ?` or `{self.prefix}hinfo ?` for more info.", inline=False)

            self.bot.logger.log(f'{ctx.message.author} gave an invalid input for herb command.')

        if discord.ChannelType == "private":
            await message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

    #----------------------------
    # Potion Command
    #----------------------------
    @commands.command(extras=["f':alembic:  **__Potion__**'", "f'**Usage: `{self.prefix}potion c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.'", "inline=False"])
    async def potion(self, ctx, *, select):
        if not gsa:
            return

        # Here we use .lower() to lower case all the values in select
        # before splitting them and adding them to the list "mix"
        mix = select.lower().replace("'","").split(", ")
        m_Response = ""
        ws = s.worksheet("Potion")

        if len(mix) != 0:
            # Here we used a list comprehension to create a list of the "column A"
            # values but all in lower case
            c_list = [cell.lower().replace("'","") for cell in ws.col_values(1)]
            text = [""] * len(mix)
            modifier = [""] * len(mix)

            # Here we loop through every item in mix, but also keep a count of iterations
            # we have made, which we will use later to add the "column G" element to the
            # corresponding location in the list "modifier"
            try:
                for i, value in enumerate(mix):
                    # Here we check if the value exists in the c_list
                    if value in c_list:
                        # If we find the value in the c_list, we get the index of the value in c_list
                        index = c_list.index(value)
                        modifier[i] = int(ws.cell(index + 1, 7).value)
                        if modifier[i] < 0:
                             m_Response = m_Response + ' - ' + str(modifier[i]).replace("-","")
                        else:
                            m_Response = m_Response + ' + ' + str(modifier[i])
                        text[i] = ws.cell(index+1,1).value

                c_Response = str(text).replace('"','').replace("[","").replace("]","").replace("'","")
                total = 10 + int(sum(modifier))

                self.bot.logger.log(f'A potion DC was generated.')

                file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/alembic.png'), filename='alembic.png')
                embed = discord.Embed(color=0x019cd0)
                embed.set_author(name = 'POTION DIFFICULTY', icon_url='attachment://alembic.png')
                embed.add_field(name = '__Alchemy Attempt DC__', value = f"The difficulty for a potion\poison\enchantment made from:\n{c_Response}\n\n 10 {m_Response} = **`{total}`**", inline=False)

            except Exception as e:
                self.bot.logger.log(f'there was an error: {e}')

                file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
                embed = discord.Embed(color=0xcc0000)
                embed.set_author(name='Potion', icon_url='attachment://prohibited.png')
                embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select components within the potion component list. Type `{self.prefix}potion ?`, `{self.prefix}herb list` for a list of components, or `{self.prefix}herb (name)` for details on a spicific component.", inline=False)

        elif mix == '?':
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Potion)', icon_url='attachment://warning.png')
            embed.add_field(name='**__Potion__**', value=f"**Usage: `{self.prefix}potion c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)

            self.bot.logger.log(f'{ctx.message.author} asked for help with {self.prefix}potion')


        else:
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Potion', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select components within the potion component list. Type `{self.prefix}potion ?`, `{self.prefix}herb list` for a list of components, or `{self.prefix}herb (name)` for details on a spicific component.", inline=False)

            self.bot.logger.log(f'{ctx.message.author} gave an invalid input for potion command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

    #----------------------------
    # Poison Command
    #----------------------------
    @commands.command(extras=["f':test_tube:  **__Poison__**'", "f'**Usage: `{self.prefix}poison c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.'", "inline=False"])
    async def poison(self, ctx, *, select):
        if not gsa:
            return

        # Here we use .lower() to lower case all the values in select
        # before splitting them and adding them to the list "mix"
        mix = select.lower().replace("'","").split(", ")
        m_Response = ""
        ws = s.worksheet("Poison")

        if len(mix) != 0:
            # Here we used a list comprehension to create a list of the "column A"
            # values but all in lower case
            c_list = [cell.lower().replace("'","") for cell in ws.col_values(1)]
            text = [""] * len(mix)
            modifier = [""] * len(mix)

            # Here we loop through every item in mix, but also keep a count of iterations
            # we have made, which we will use later to add the "column G" element to the
            # corresponding location in the list "modifier"

            try:
                for i, value in enumerate(mix):
                    # Here we check if the value exists in the c_list
                    if value in c_list:
                        # If we find the value in the c_list, we get the index of the value in c_list
                        index = c_list.index(value)
                        modifier[i] = int(ws.cell(index + 1, 7).value)
                        if modifier[i] < 0:
                            m_Response = m_Response + ' - ' + str(modifier[i]).replace("-","")
                        else:
                            m_Response = m_Response + ' + ' + str(modifier[i])
                            text[i] = ws.cell(index+1,1).value


                    c_Response = str(text).replace('"','').replace("[","").replace("]","").replace("'","")
                    total = 10 + int(sum(modifier))

                    self.bot.logger.log(f'A poison DC was generated.')

                    file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/test-tube.png'), filename='test-tube.png')
                    embed = discord.Embed(color=0x019cd0)
                    embed.set_author(name = 'POISON DIFFICULTY', icon_url='attachment://test-tube.png')
                    embed.add_field(name = '__Alchemy Attempt DC__', value = f"The difficulty for a poison made from:\n{c_Response}\n\n 10 {m_Response} = **`{total}`**", inline=False)

            except Exception as e:
                self.bot.logger.log(f'There was an error.: {e}')

                file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
                embed = discord.Embed(color=0xcc0000)
                embed.set_author(name='Poison', icon_url='attachment://prohibited.png')
                embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select components within the poison component list. Type `{self.prefix}poison ?` or `{self.prefix}herb list` for more info.", inline=False)

        elif mix == '?':
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Poison)', icon_url='attachment://warning.png')
            embed.add_field(name='**__Poison__**', value=f"**Usage: `{self.prefix}poison c `\nwhere `c = component` multiple components separated by a `,`**\nValid component selections can be found by using `{self.prefix}herb list` for a list of components or `{self.prefix}herb (name)` for details on a spicific component you wish to combine for effects.", inline=False)

            self.bot.logger.log(f'{ctx.message.author} asked for help with {self.prefix}poison')

        else:
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Poison', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select components within the poison component list. Type `{self.prefix}poison ?`, `{self.prefix}herb list` for a list of components, or `{self.prefix}herb (name)` for details on a spicific component.", inline=False)

            self.bot.logger.log(f'{ctx.message.author} gave an invalid input for poison command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Components(bot))
