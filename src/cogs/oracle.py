import discord
import os, datetime
import random
from discord.ext import commands

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
        self.bot.logger.log(f'Is seeing into the beyond.')



    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            self.bot.logger.log(f'missing or invalid argument for oracle')
            m_Response = f"That's not a valid input. Please try again or `self.bot.config.get().prefixoracle ?` for more information."
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Oracle', icon_url='attachment://prohibited.png')
            embed.add_field(name='**__Error__**', value=f"{m_Response}", inline=False)
            if discord.ChannelType == "private":
                self.bot.logger.log(f"{ctx.message.author} has asked the oracle something it doesn't understand")
                await ctx.message.author.send(file=file, embed=embed)
            elif discord.ChannelType != "private":
                self.bot.logger.log(f"{ctx.message.author} has asked the oracle something it doesn't understand")
                await ctx.send(file=file, embed=embed)


    @commands.command()
    async def oracle(self, ctx, *, question):



        replies = ["Yes.", "No.", "I said NO!", "Do you really want an answer to that?", "Ask again later.", "Go play in the street.", "Shut your cock holster!","How can you even ask something like that?", "If you don't know the answer already I certainly can't help you.", "Lets be honest you could use the life experience.", "Lets just say... your best option would be to put your head between your legs and kiss your ass goodbye.", "Definitely maybe.", "Ask me again someday.", "*~Unintelligable, Yet Frightening Wispers~*","*~Disembodied Laughter of Children~*"];
        if (int(question.count(" ")) >= 2):
            file = discord.File('./eyebot/images/commands/crystal-ball.png', filename='crystal-ball.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Oracle', icon_url='attachment://crystal-ball.png')
            embed.add_field(name='__Response__', value=random.choice(replies), inline=False)

            if discord.ChannelType == "private":
                self.bot.logger.log(f'{ctx.message.author} has sought guidance.')
                await ctx.message.author.send(file=file, embed=embed)
            elif discord.ChannelType != "private":
                self.bot.logger.log(f'{ctx.message.author} has sought guidance.')
                await ctx.send(file=file, embed=embed)

        elif question == '?':
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Oracle)', icon_url='attachment://warning.png')
            embed.add_field(name=f"**__Oracle__**", value=f"**Usage: `self.bot.config.get().prefixoracle q`\n Where `question = the question you want to ask`**\nSimple general responses to questions. Careful the oracle can be a bit sassy!", inline=False)
            if discord.ChannelType == "private":
                self.bot.logger.log(f'{ctx.message.author} asked for help with oracle')
                await ctx.message.author.send(file=file, embed=embed)
            elif discord.ChannelType != "private":
                self.bot.logger.log(f'{ctx.message.author} asked for help with oracle')
                await ctx.send(file=file, embed=embed)

        else:
            m_Response = f"That's not a valid input. Please try again or `self.bot.config.get().prefixoracle ?` for more information."
            file = discord.File('./eyebot/images/system/prohibited.png', filename='prohibited.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Oracle', icon_url='attachment://prohibited.png')
            embed.add_field(name='**__Error__**', value=f"{m_Response}", inline=False)
            if discord.ChannelType == "private":
                self.bot.logger.log(f"{ctx.message.author} has asked the oracle something it doesn't understand")
                await ctx.message.author.send(file=file, embed=embed)
            elif discord.ChannelType != "private":
                self.bot.logger.log(f"{ctx.message.author} has asked the oracle something it doesn't understand")
                await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(Oracle(bot))
