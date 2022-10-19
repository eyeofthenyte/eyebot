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
        self.config = bot.config
        self.prefix = self.config["prefix"]


    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Core functions started.")

    async def cog_command_error(self, ctx, error):
        self.logger.error(f'Admin encountered error: %s', error)
        if isinstance(error, commands.CommandError):
            self.logger.error("There was an error with Admin commands.")
            await ctx.send('Something went wrong.')



    # ---------------------------------------------------------
    # Administrative Commands
    # ---------------------------------------------------------
    #Shutdown bot
    @commands.command(aliases=['shtudown','sd'], extras=["f':octagonal_sign: **__Shutdown__**'", "f'Terminates bot all bot functions. Need to be bot owner to use. Contact Eyeofthenyte#0042 with any issues.'", "inline=False"])
    @commands.is_owner()
    async def _shutdown(self,ctx):
        try:
            await ctx.send("Shutting down the bot...")
            await self.bot.close()

        except Exception as e:
            self.bot.logger.log(f'{e}')     
            await ctx.send("There was a problem shutting down the bot. You might not be the bot owner.")

    #Disconnect bot from server BOT OWNER ONLY
    @commands.command(extras=["f':wave:  **__Leave__**'", "f'**Usage: `{self.prefix}leave server`\nWhere `server = name of server`**\nWill make the bot leave the server.\n**Must be server owner to use this command.**\n'", "inline=False"])
    @commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
    async def leave(self, ctx, *, guild_name):
        guild = discord.utils.get(bot.guilds, name=guild_name)
        if guild is None:
            await ctx.send("I don't recognize that guild. Please enter the server name. (case sensitive)")
            logger.error(f'leaving_error - blank or invalid server name, please enter the guild name')
            return
        else:
            await guild.leave()
            logger.error(f'connection_broken: {bot.user.name} has left: {guild.name} (id: {guild.id})')

    #Check connected servers BOT OWNER ONLY
    @commands.command(extras=["f':computer: **__Servers__**', "f'A listing of servers the bot is curretntly connected to. Need to be bot owner to use. Contact Eyeofthenyte#0042 with any issues.', "inline=False"])
    @commands.is_owner()
    async def servers(self, ctx):
        for guild in self.bot.guilds:
            self.logger.info(f'%-10s(id: %s)%-5s-%-5s', ' ', bot.guild.id, ' ', ' ', bot.guild.name)
            await ctx.author.send(f'%-5s(id: %s)%-5s-%-5s%s', ' ', bot.guild.id, ' ', ' ', bot.guild.name)
        logger.info(f'-End of Server Listing-')


async def setup(bot):
    await bot.add_cog(Admin(bot))
