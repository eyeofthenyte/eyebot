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
    @commands.command(aliases=['shutdown','sd'])
    @commands.is_owner()
    async def _shutdown(self,ctx):
        """
        🔒 Gracefully shuts down the bot.

        Usage:
        `!shutdown`

        Aliases:`!sd`, `!_shutdown`
        
        Access: Bot Owner Only
        """


        try:
            await ctx.send("Shutting down the bot...")
            await self.bot.close()

        except Exception as e:
            self.bot.logger.log(f'{e}')     
            await ctx.send("There was a problem shutting down the bot. You might not be the bot owner.")

    #Disconnect bot from server BOT OWNER ONLY
    @commands.command()
    @commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
    async def leave(self, ctx, *, guild_name):
        """
        📤 Forces the bot to leave a server by its name.

        Usage:
        `!leave <Server Name>`

        Example:
        `!leave My Cool Server`

        Note: Server name is case-sensitive
        Access: Server Administrator or Bot Owner
        """

        guild = discord.utils.get(bot.guilds, name=guild_name)
        if guild is None:
            await ctx.send("I don't recognize that guild. Please enter the server name. (case sensitive)")
            logger.error(f'leaving_error - blank or invalid server name, please enter the guild name')
            return
        else:
            await guild.leave()
            logger.error(f'connection_broken: {bot.user.name} has left: {guild.name} (id: {guild.id})')

    #Check connected servers BOT OWNER ONLY
    @commands.command()
    @commands.is_owner()
    async def servers(self, ctx):
        """
        📋 Lists all servers the bot is currently connected to via DM.\n"

        Usage:
        `!servers`

        Access: Bot Owner Only
        """

        for guild in self.bot.guilds:
            self.logger.info(f'%-10s(id: %s)%-5s-%-5s', ' ', bot.guild.id, ' ', ' ', bot.guild.name)
            await ctx.author.send(f'%-5s(id: %s)%-5s-%-5s%s', ' ', bot.guild.id, ' ', ' ', bot.guild.name)
        logger.info(f'-End of Server Listing-')


async def setup(bot):
    await bot.add_cog(Admin(bot))
