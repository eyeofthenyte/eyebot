import sys, discord
import os, json, datetime, codecs, re
import random
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find
from eyebot import t

# ---------------------------------------------------------
# Found Gems Generator
# ---------------------------------------------------------
class Gems(commands.Cog):
    
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
            print(f'{t()}: missing or invalid argument for .gems')
            if discord.ChannelType == "private":
                await message.author.send(embed=embed)
                return
            else:
                await ctx.send(f'Make sure you put in the value in gp and the quantiy of gems you wish to generate. i.e. `.gems 100 5`')
                return


    #----------------------------
    # Gems Command
    #----------------------------
    @commands.command()
    async def gems(self, ctx, *, gemstring):
        await ctx.message.delete()
        #----------------------------
        # Variables
        #----------------------------
        m_Response = ""
        randline = ""
        ckstr = bool(re.search(r"\s", gemstring))
        lstr = len(gemstring)
        gems=[]

        #----------------------------
        # Gem Table Selection
        #----------------------------
        #await ctx.send("__**The gems that you found are:**__")
        if ckstr == True:
            gemstring = gemstring.split()
            select = gemstring[0]
            i = int(gemstring[1])
            while i > 0:
                lines = open(os.path.join(os.path.dirname(__file__), f"./gems/{select}gp.txt")).read().splitlines()
                randline = random.choice(lines)
                list = randline.split(";")
                m_Response = f'- {list[0]}: {list[1]}'
                gems.append(m_Response)
                i -= 1

            embed = discord.Embed(color=0x019cd0)
            embed.set_thumbnail(url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/google/346/gem-stone_1f48e.png')
            embed.set_author(name = 'RANDOM GEM SELECTION')
            embed.add_field(name = 'You discovered the following {select} gems:', value = '\n'.join(gems), inline=False)

            if discord.ChannelType == "private":
                await message.author.send(embed=embed)
            else:
                await ctx.send(embed=embed)

        else:
            if lstr == 1 and gemstring == '?':
                print(f"{t()}: {ctx.message.author}({ctx.message.author.guild}) asked for help with .gems command")
                embed = discord.Embed(color=0x019cd0)
                embed.set_author(name='Help (Gems)')
                embed.add_field(name=':gem:  **__Gems__**', value='**Usage: `.gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`     n = number of gems to be generated`**\n The value of gems corresponds to the Gem Tables DMG - Chapter 7.\nThis will generate a number of gems of a single gold value type based the table selected.', inline=False)
                if discord.ChannelType == "private":
                    await message.author.send(embed=embed)
                else:
                    await ctx.send(embed=embed)

            else:
                print(t() + " : ({ctx.message.author.guild}) entered invalid argument")
                embed = discord.Embed(color=0x019cd0)
                embed.set_author(name='Help (Gems)')
                embed.add_field(name=':gem:  **__Gems__**', value='**Usage: `.gems g n` \nwhere `g = value of gems desired`**\n*10, 50, 100, 500, 1000, 5000*\n**`     n = number of gems to be generated`**\n The value of gems corresponds to the Gem Tables DMG - Chapter 7.\nThis will generate a number of gems of a single gold value type based the table selected.', inline=False)
                if discord.ChannelType == "private":
                    await message.author.send(embed=embed)
                else:
                    await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Gems(bot))
