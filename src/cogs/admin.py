import logging
from services.logService import LogService
from discord.ext import commands

# ---------------------------------------------------------
# Admin Commands
# ---------------------------------------------------------
class Admin (commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Core functions started.")

    async def cog_command_error(self, ctx, error):
        self.logger.error(f'Admin encountered error: %s', error)
        if isinstance(error, commands.CommandError):
            self.logger.error("there was an error with Admin commands.")
            await ctx.send('Something went wrong.')

    @commands.command(aliases=['shtudown','sd'])
    async def _shutdown(self,ctx: commands.bot.Context) -> None:
        if ctx.author.name != ctx.bot.connected_channels[0].name:
            await ctx.send("You cannot shut the bot down.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
