import os, datetime, gspread
import discord
import yaml
import random
from discord.ext import commands
from yaml.loader import SafeLoader

gsa = gspread.service_account(filename = 'eyebot/service_account.json')

s = gsa.open_by_key('1dwpn9CbEtwlkfzH4Qh0KafwZ2kvWarrDJCqPuR3fe0Q')
sheet_list = s.worksheets()
for i in range(len(sheet_list)):
    shname = str(sheet_list[i]).split("'")
    sheet_list[i] = shname[1]
del sheet_list[-1]

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

#Pass Bot Prefix
def get_prefix():
    with open('./eyebot/config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        BOT_PREFIX = "!"
        if data["prefix"]:
            BOT_PREFIX = config["prefix"]
        return BOT_PREFIX


prefix = get_prefix()

class Trinket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Staring at the shinies.')

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            print(f'{t()}: {ctx.message.author}is missing or invalid argument for {prefix}trinket')
            error_m = f'Please select one of the following classes:\n' + str(sheet_list).replace("'","").replace("[","").replace("]","") + f'.\n Type `{prefix}trinket ?` for more info.'
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Trinket', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f'{error_m}', inline=False)
            if discord.ChannelType == "private":
                await ctx.message.author.send(file=file, embed=embed)
            elif discord.ChannelType != "private":
                await ctx.send(file=file, embed=embed)


    #----------------------------
    # Trinkets Command
    #----------------------------
    @commands.command()
    async def trinket(self, ctx, *, select):
        if select.lower() in str(sheet_list).lower():
            for i in range(len(sheet_list)):
                if select.lower() == sheet_list[i].lower():
                    worksheet = s.worksheet(str(sheet_list[i]))
                    v_list = worksheet.col_values(2)
                    v_list = list(filter(None, v_list))
                    file = discord.File('./eyebot/images/classes/'+select.lower()+'.jpeg', filename=select.lower()+'.jpeg')
                    print(f'{t()}: {ctx.message.author} drew a random trinket from the ' + select.upper() + ' list.')
                    embed = discord.Embed(color=0x019cd0)
                    embed.set_thumbnail(url = 'attachment://'+select.lower()+'.jpeg')
                    embed.set_author(name = select.upper() + ' TRINKET')
                    embed.add_field(name = 'You found the following:', value=random.choice(v_list), inline=False)


        elif select == '?':
            print(f'{t()}: {ctx.message.author} asked for help with {prefix}trinket command.')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Trinket)', icon_url='attachment://warning.png')
            embed.add_field(name='**__Trinket__**', value="**Usage: `{prefix}trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.", inline=False)

        else:
            print(f'{t()}: there was an error.')
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Trinket', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select an available Character Class. Type `trinket ?` for more info.", inline=False)
            print(f'{t()}: Invalid input for {prefix}trinket command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(Trinket(bot))
