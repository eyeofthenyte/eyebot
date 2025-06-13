import os
import discord
from services.logService import LogService
from discord.ext import commands
from typing import Optional



class Help (commands.Cog):
    # ---------------------------------------------------------
    # Commands Listing
    # ---------------------------------------------------------
    @commands.command(name="commands")
    async def list_commands(self, ctx):
        """Lists all commands grouped by Cog."""
        embed = discord.Embed(
            title="📜 All Commands",
            description="Commands are grouped by their module (Cog). Use `!help <command>` for details.",
            color=discord.Color.blurple()
        )

        for cog_name, cog in self.bot.cogs.items():
            command_list = []
            for command in cog.get_commands():
                aliases = f" (aliases: {', '.join(command.aliases)})" if command.aliases else ""
                command_list.append(f"`{command.name}`{aliases}")
            if command_list:
                embed.add_field(name=f"📦 {cog_name}", value="\n".join(command_list), inline=False)

        await ctx.send(embed=embed)


    # ---------------------------------------------------------
    # Help Command
    # ---------------------------------------------------------
    @commands.command(name="help")
    async def help_command(self, ctx, *, command_name: Optional[str] = None):
        """Shows help for a specific command."""
        if not command_name:
            return await ctx.send("❓ Use `!commands` to see all commands or `!help <command>` for specific help.")

        command = self.bot.get_command(command_name)
        if not command:
            return await ctx.send(f"❌ Command `{command_name}` not found.")

        embed = discord.Embed(
            title=f"❔ Help: `{command.name}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Description", value=command.help or "No description provided.", inline=False)

        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in command.aliases), inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
