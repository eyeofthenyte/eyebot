import sys, discord
import os, json, datetime, codecs, re
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find
from eyebot import t



# ---------------------------------------------------------
# Die Roller
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
            print(f'{t()}: missing or invalid argument for .oracle')
            await ctx.send('Usage: `.oracle question` e.g. `.oracle is this going to work?`\nUse .oracle ? for more info.')
        

    @commands.command()
    async def oracle(self, ctx, *, question):
        await ctx.message.delete()
        replies = ["Yes.", "No.", "I said NO!", "Do you really want an answer to that?", "Ask again later.", "Go play in the street.", "Shut your cock holster!","How can you even ask something like that?", "If you don't know the answer already I certainly can't help you.", "Lets be honest you could use the life experience.", "Lets just say... your best option would be to put your head between your legs and kiss your ass goodbye.", "Definitely maybe.", "Ask me again someday.", "*~Unintelligable, Yet Frightening Wispers~*","*~Disembodied Laughter of Children~*"];
        if (int(question.count(" ")) >= 2):
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Oracle', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/crystal-ball_1f52e.png')
            embed.add_field(name='__Response__', value=random.choice(replies), inline=False)
            print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) has sought guidance.')
            await ctx.send(embed=embed)
        
        elif question == '?':
            print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) asked for help with .oracle')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Oracle)', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/warning_26a0.png')
            embed.add_field(name=f"**__Oracle__**", value=f"**Usage: `.oracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
            await ctx.send(embed=embed)
                         
        else:
            m_Response = "That's not a valid input. Please try again or `.oracle ?` for more information."
            print(f"{t()}: {ctx.message.author}({ctx.message.author.guild}) has asked the oracle something it doesn't understand")
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Oracle', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='**__Error__**', value=f"{m_Response}", inline=False) 
            await ctx.send(embed=embed)
            

def setup(bot):
    bot.add_cog(Oracle(bot))