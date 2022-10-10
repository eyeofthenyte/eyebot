import os, datetime
import discord
from discord.ext import commands

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

# ---------------------------------------------------------
# Admin Commands
# ---------------------------------------------------------
class Admin (commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Core functions started.')

    async def cog_command_error(self, ctx, error):
        print(f'Admin encountered error {error}')
        if isinstance(error, commands.CommandError):
            print(f'{t()}: there was an error with Admin commands.')
            await ctx.send('Something went wrong.')


    @commands.command(aliases=['shtudown','sd'])
    async def _shutdown(self,ctx: commands.bot.Context) -> None:
        if ctx.author.name != ctx.bot.connected_channels[0].name:
            await ctx.send("You cannot shut the bot down.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
