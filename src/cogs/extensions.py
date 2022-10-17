import discord
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
        try:
            await self.bot.load_extension(f'cogs.{extension}')
            self.bot.logger.log(f'Loaded extension - "{extension}"')
            file = discord.File('./eyebot/images/commands/thumbs-up.png', filename='thumbs-up.png')
            embed = discord.Embed(color=0x01f31d)
            embed.set_author(name = 'LOADED ' + extension.upper(), icon_url = 'attachment://thumbs-up.png')
            embed.add_field(name = '**__Extension Load__**', value = 'Extension: "' + extension + '" has been loaded successfully.', inline=False)
        except Exception as e:
            self.bot.logger.log(f'{e}')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name = 'LOADING ' + extension.upper() + ' FAILED', icon_url = 'attachment://warning.png')
            embed.add_field(name = '**__Extension Load__**', value = e, inline=False)

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

    #----------------------------
    # Unload Command
    #----------------------------
    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            self.bot.logger.log(f'Unloaded extension - "{extension}"')
            file = discord.File('./eyebot/images/commands/thumbs-up.png', filename='thumbs-up.png')
            embed = discord.Embed(color=0x01f31d)
            embed.set_author(name = 'UNLOADED ' + extension.upper(), icon_url = 'attachment://thumbs-up.png')
            embed.add_field(name = '**__Extension Unload__**', value = 'Extension: "' + extension + '" has been unloaded.', inline=False)

        except Exception as e:
            self.bot.logger.log(f'{e}')
            file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name = 'UNLOADING ' + extension.upper() + ' FAILED', icon_url = 'attachment://warning.png')
            embed.add_field(name = '**__Extension Unload__**', value =  e, inline=False)

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)


    #----------------------------
    # Reload Command
    #----------------------------
    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        self.bot.logger.log(f'Attempting to reload {extension}')
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
                file = discord.File('./eyebot/images/commands/thumbs-up.png', filename='thumbs-up.png')
                embed = discord.Embed(color=0x01f31d)
                embed.set_author(name = 'RELOADED ' + extension.upper(), icon_url = 'attachment://thumbs-up.png')
                embed.add_field(name = '**__Extension Reload__**', value='Reloading "' + extension + '" has been completed successfully.', inline=False)

            except Exception as e:
                self.bot.logger.log(f'    - {e}')
                self.bot.logger.log(f'Reload extension - "{extension}" has failed.')
                file = discord.File('./eyebot/images/system/warning.png', filename='warning.png')
                embed = discord.Embed(color=0xcc0000)
                embed.set_author(name = 'RELOADING ' + extension.upper() + ' FAILED', icon_url = 'attachment://warning.png')
                embed.add_field(name = '**__Extension Reload__**', value='Reloading "' + extension + '" has failed. Invalid extension or extension not loaded.', inline=False)

        except Exception as e:
            self.bot.logger.log(f'{e}')

        if discord.ChannelType == "private":
            await ctx.message.author.send(file=file, embed=embed)
        elif discord.ChannelType != "private":
            await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Extensions(bot))
