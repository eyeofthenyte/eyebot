import sys, discord
import os, json, datetime, codecs, re
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find

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
# Oracle
# ---------------------------------------------------------
class Oracle (commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Is seeing into the beyond.')
            


    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            print(f'{t()}: missing or invalid argument for oracle')
            if discord.ChannelType == "private":
                await message.author.send(f'Usage: `{prefix}oracle question` e.g. `{prefix}oracle is this going to work?`\nUse {self.command_prefix}oracle ? for more info.')
            elif discord.ChannelType != "private":
                await ctx.send(f'Usage: `.oracle question` e.g. `{prefix}oracle is this going to work?`\nUse oracle ? for more info.')
        

    @commands.command()
    async def oracle(self, ctx, *, question):



        replies = ["Yes.", "No.", "I said NO!", "Do you really want an answer to that?", "Ask again later.", "Go play in the street.", "Shut your cock holster!","How can you even ask something like that?", "If you don't know the answer already I certainly can't help you.", "Lets be honest you could use the life experience.", "Lets just say... your best option would be to put your head between your legs and kiss your ass goodbye.", "Definitely maybe.", "Ask me again someday.", "*~Unintelligable, Yet Frightening Wispers~*","*~Disembodied Laughter of Children~*"];
        if (int(question.count(" ")) >= 2):
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Oracle', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/crystal-ball_1f52e.png')
            embed.add_field(name='__Response__', value=random.choice(replies), inline=False)

            if discord.ChannelType == "private":
                print(f'{t()}: {ctx.message.author} has sought guidance.')
                await ctx.message.author.send(embed=embed)
            elif discord.ChannelType != "private":
                print(f'{t()}: {ctx.message.author} has sought guidance.')
                await ctx.send(embed=embed)
        
        elif question == '?':
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Oracle)', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/warning_26a0.png')
            embed.add_field(name=f"**__Oracle__**", value=f"**Usage: `{prefix}oracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
            if discord.ChannelType == "private":
                print(f'{t()}: {ctx.message.author} asked for help with oracle')
                await ctx.message.author.send(embed=embed)
            elif discord.ChannelType != "private":
                print(f'{t()}: {ctx.message.author} asked for help with oracle')
                await ctx.send(embed=embed)
                         
        else:
            m_Response = f"That's not a valid input. Please try again or `{self.command_prefix}oracle ?` for more information."
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Oracle', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='**__Error__**', value=f"{m_Response}", inline=False) 
            if discord.ChannelType == "private":
                print(f"{t()}: {ctx.message.author} has asked the oracle something it doesn't understand")
                await ctx.message.author.send(embed=embed)
            elif discord.ChannelType != "private":
                print(f"{t()}: {ctx.message.author} has asked the oracle something it doesn't understand")
                await ctx.send(embed=embed)
            

def setup(bot):
    bot.add_cog(Oracle(bot))
