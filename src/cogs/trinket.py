import gspread
import random
import logging
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

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Staring at the shinies.')

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'{ctx.message.author}is missing or invalid argument for {self.bot.config.get().prefix}trinket')
            error_m = f'Please select one of the following classes:\n' + str(sheet_list).replace("'","").replace("[","").replace("]","") + f'.\n Type `{self.bot.config.get().prefix}trinket ?` for more info.'
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
                    self.bot.logger.log(f'{ctx.message.author} drew a random trinket from the ' + select.upper() + ' list.')
                    embed = discord.Embed(color=0x019cd0)
                    embed.set_thumbnail(url = 'attachment://'+select.lower()+'.jpeg')
                    embed.set_author(name = select.upper() + ' TRINKET')
                    embed.add_field(name = 'You found the following:', value=random.choice(v_list), inline=False)


        elif select == '?':
            self.bot.logger.log(f'{ctx.message.author} asked for help with {self.bot.config.get().prefix}trinket command.')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Trinket)', icon_url='attachment://warning.png')
            embed.add_field(name='**__Trinket__**', value="**Usage: `{self.bot.config.get().prefix}trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.", inline=False)

        else:
            self.bot.logger.log(f'there was an error.')
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Trinket', icon_url='attachment://prohibited.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select an available Character Class. Type `trinket ?` for more info.", inline=False)
            self.bot.logger.log(f'Invalid input for {self.bot.config.get().prefix}trinket command.')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(Trinket(bot))
