import discord
import os
import logging
from services.logService import LogService
from discord.ext import commands

# ---------------------------------------------------------
# Extension Related Commands
# ---------------------------------------------------------
class Extensions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Has made external connections.')


    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Missing argument')
            self.bot.logger.log(f'missing argument')
            return


    #----------------------------
    # Load Command
    #----------------------------

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, extension):
        """
        Loads a cog (extension) into the bot.

        Usage:
            !load <extension>

        Parameters:
            extension (str): The name of the cog to load (e.g., 'music', 'admin').

        Description:
            This command attempts to load the specified cog from the `cogs` directory.
            Use this after unloading a cog or when adding new functionality dynamically.
            Only the bot owner can run this command.

        Responses:
            Success - Confirmation embed that the extension was loaded.
            Failure - Error embed explaining why the loading failed.
        """

        self.bot.logger.log(f'Attempting to load {extension}')

        icon = None
        embed = discord.Embed(
            title="⚠️ Load Failed",
            description=f"An unexpected error occurred while loading `{extension}`.",
            color=discord.Color.red()
        )

        try:
            await self.bot.load_extension(f'cogs.{extension}')
            self.bot.logger.log(f'Loaded extension - "{extension}" successfully.')
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/thumbs-up.png'), filename='thumbs-up.png')
            embed = discord.Embed(color=0x01f31d)
            embed.set_author(name='LOADED ' + extension.upper(), icon_url='attachment://thumbs-up.png')
            embed.add_field(name='**__Extension Load__**', value=f'Extension: "{extension}" has been loaded successfully.', inline=False)
        except Exception as e:
            self.bot.logger.log(f'{e}')
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='LOADING ' + extension.upper() + ' FAILED', icon_url='attachment://warning.png')
            embed.add_field(name='**__Extension Load__**', value=e, inline=False)

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.author.send(file=icon, embed=embed)
        else:
            await ctx.send(file=icon, embed=embed)

    #----------------------------
    # Unload Command
    #----------------------------
    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        """
        Unloads a cog (extension) from the bot.

        Usage:
            !unload <extension>

        Parameters:
            extension (str): The name of the cog to unload (e.g., 'music', 'admin').

        Description:
            This command attempts to unload the specified cog from the bot.
            Use this to disable a cog, often useful when troubleshooting or updating cogs.
            Only the bot owner can run this command.

        Responses:
            Success - Confirmation embed that the extension was unloaded.
            Failure - Error embed explaining why the unloading failed.
        """

        self.bot.logger.log(f'Attempting to unload {extension}')

        icon = None
        embed = discord.Embed(
            title="⚠️ Unload Failed",
            description=f"An unexpected error occurred while unloading `{extension}`.",
            color=discord.Color.red()
        )


        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            self.bot.logger.log(f'Unloaded extension - "{extension}" successfully.')
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/thumbs-up.png'), filename='thumbs-up.png')
            embed = discord.Embed(color=0x01f31d)
            embed.set_author(name='UNLOADED ' + extension.upper(), icon_url='attachment://thumbs-up.png')
            embed.add_field(name='**__Extension Unload__**', value=f'Extension: "{extension}" has been unloaded.', inline=False)

        except Exception as e:
            self.bot.logger.log(f'{e}')
            icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='UNLOADING ' + extension.upper() + ' FAILED', icon_url='attachment://warning.png')
            embed.add_field(name='**__Extension Unload__**', value=e, inline=False)

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.author.send(file=icon, embed=embed)
        else:
            await ctx.send(file=icon, embed=embed)


    #----------------------------
    # Reload Command
    #----------------------------
    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        """
        Reloads a cog (extension) in the bot.

        Usage:
            !reload <extension>

        Parameters:
            extension (str): The name of the cog to reload (e.g., 'music', 'admin').

        Description:
            This command unloads and then loads the specified cog again.
            It is useful to apply changes made to the cog's code without restarting the bot.
            Only the bot owner can run this command.

        Responses:
            Success - Confirmation embed that the extension was reloaded.
            Failure - Error embed explaining why the reload failed.
        """

        self.bot.logger.log(f'Attempting to reload {extension}')

        # Set safe defaults for fallback
        icon = None
        embed = discord.Embed(
            title="⚠️ Reload Failed",
            description=f"An unexpected error occurred while reloading `{extension}`.",
            color=discord.Color.red()
        )

        try:
            try:
                await self.bot.unload_extension(f'cogs.{extension}')
                self.bot.logger.log(f'    - "{extension}" has been unloaded.')

            except Exception as e:
                await self.bot.logger.log(f'    - {e}')

            try:
                await self.bot.load_extension(f'cogs.{extension}')
                self.bot.logger.log(f'    - "{extension}" has been loaded.')
                self.bot.logger.log(f'Reloaded extension - "{extension}" successfully.')
                icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/commands/thumbs-up.png'), filename='thumbs-up.png')
                embed = discord.Embed(color=0x01f31d)
                embed.set_author(name='RELOADED ' + extension.upper(), icon_url='attachment://thumbs-up.png')
                embed.add_field(name='**__Extension Reload__**', value=f'Reloading "{extension}" has been completed successfully.', inline=False)

            except Exception as e:
                self.bot.logger.log(f'    - {e}')
                self.bot.logger.log(f'Reload extension - "{extension}" has failed.')
                icon = discord.File(os.path.join(os.path.dirname(__file__), '../../images/system/warning.png'), filename='warning.png')
                embed = discord.Embed(color=0xcc0000)
                embed.set_author(name='RELOADING ' + extension.upper() + ' FAILED', icon_url='attachment://warning.png')
                embed.add_field(name='**__Extension Reload__**', value=f'Reloading "{extension}" has failed. Invalid extension or extension not loaded.', inline=False)

        except Exception as e:
            self.bot.logger.log(f'{e}')
            embed.description += f"\n\nException: `{e}`"

        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.author.send(file=icon, embed=embed) if icon else await ctx.author.send(embed=embed)
        else:
            await ctx.send(file=icon, embed=embed) if icon else await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Extensions(bot))
