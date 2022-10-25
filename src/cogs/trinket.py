import os
import discord
import gspread
import random
from services.logService import LogService
from discord.ext import commands

gsa = 0
sheet_list = []

if os.path.exists(os.path.dirname(__file__) + '/../../service_account.json'):
    gsa = gspread.service_account(filename = os.path.dirname(__file__) + '/../../service_account.json')

    s = gsa.open_by_key('1dwpn9CbEtwlkfzH4Qh0KafwZ2kvWarrDJCqPuR3fe0Q')
    sheet_list = s.worksheets()
    for i in range(len(sheet_list)):
        shname = str(sheet_list[i]).split("'")
        sheet_list[i] = shname[1]
    del sheet_list[-1]

class Trinket(commands.Cog):

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
        self.bot.logger.log(f'Staring at the shinies.')

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'{ctx.message.author}is missing or invalid argument for !trinket')
            error_m = f'Please select one of the following classes:\n' + str(sheet_list).replace("'","").replace("[","").replace("]","") + f'.\n Type `!trinket ?` for more info.'
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
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
    @commands.command(extras=[":ring:  **__Trinket__**", "**Usage: `!trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket tables.\n"])
    async def trinket(self, ctx, *, select):
        if select.lower() in str(sheet_list).lower():
            for i in range(len(sheet_list)):
                if select.lower() == sheet_list[i].lower():
                    worksheet = s.worksheet(str(sheet_list[i]))
                    v_list = worksheet.col_values(2)
                    v_list = list(filter(None, v_list))
                    file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/classes/'+select.lower()+'.jpeg'), filename=select.lower()+'.jpeg')
                    self.bot.logger.log(f'{ctx.message.author} drew a random trinket from the ' + select.upper() + ' list.')
                    embed = discord.Embed(color=0x019cd0)
                    embed.set_thumbnail(url = 'attachment://'+select.lower()+'.jpeg')
                    embed.set_author(name = select.upper() + ' TRINKET')
                    embed.add_field(name = 'You found the following:', value=random.choice(v_list), inline=False)

        else:
            self.bot.logger.log(f'there was an error.')
            file = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/prohibited.png'), filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Trinket', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select an available Character Class. Type `!help trinket` for more info.", inline=False)
            self.bot.logger.log(f'Invalid input for !trinket command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(Trinket(bot))
