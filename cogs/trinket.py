import sys, discord
import os, json, datetime, codecs, re, gsheets, gspread
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find
from eyebot import t
from gsheets import Sheets

gsa = gspread.service_account(filename = 'eyebot/service_account.json')

s = gsa.open_by_key('1dwpn9CbEtwlkfzH4Qh0KafwZ2kvWarrDJCqPuR3fe0Q')
sheet_list = s.worksheets()
for i in range(len(sheet_list)):
    shname = str(sheet_list[i]).split("'")
    sheet_list[i] = shname[1]
del sheet_list[-1]
icon = ["https://media-waterdeep.cursecdn.com/avatars/13916/408/637411847943829485.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/0/636336416778392507.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/1/636336416923635770.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/2/636336417054144618.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/3/636336417152216156.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/4/636336417268495752.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/5/636336417372349522.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/6/636336417477714942.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/7/636336417569697438.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/8/636336417681318097.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/9/636336417773983369.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/12/636336422983071263.jpeg","https://media-waterdeep.cursecdn.com/avatars/10/11/636336418370446635.jpeg","https://media-waterdeep.cursecdn.com/avatars/8551/969/637158853102614868.png"]


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
            print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) is missing or invalid argument for .trinket')
            await ctx.send(f'Please select one of the following classes:\n' + str(sheet_list).replace("'","").replace("[","").replace("]","") + f'.\n Type `.trinket ?` for more info.')
            return

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
                    print(f'{t()}: A random trinket from the ' + select.upper() + ' List was drawn.')
                    embed = discord.Embed(color=0x019cd0)
                    embed.set_thumbnail(url = str(icon[i]))
                    embed.set_author(name = select.upper() + ' TRINKET')
                    embed.add_field(name = 'You found the following:', value=random.choice(v_list), inline=False)


        elif select == '?':
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Trinket)', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/warning_26a0.png')
            embed.add_field(name='**__Trinket__**', value="**Usage: `.trinket c ` \nwhere `c = character class`**\nCharacter class referrs to Dungeons and Dragons character classes.\nThis data is taken from [Ted's (Nerd Immersion)](https://www.youtube.com/c/NerdImmersion1 'Nerd Immersion') random trinket's tables.", inline=False)
            print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) asked for help.')


        else:
            print(f'{t()}: there was an error.')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Trinket', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='__Error__', value=f"That was not a valid choice. Please select an available Character Class. Type `.trinket ?` for more info.", inline=False)     
            print(f'{t()}: Invalid input for wildmagic command.')

        if discord.ChannelType == "private":
            await message.author.send(embed=embed)
        else:
            await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(Trinket(bot))
