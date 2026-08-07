import discord
from discord.ext import commands
import subprocess
import random
import os
import logging
from services.logService import LogService


class NameGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.script_dir = os.path.join(os.path.dirname(__file__), "namegen")  # path to /namegen directory


    @commands.command(name="namegen")
    async def namegen(self, ctx, *args):
        """
        Generate fantasy names.
        `!namegen` -> will list the available races
        `!namegen` `race` `gender` `quantity` -> Will generate a number of names based on race and gender
        `!namegen` `gender` `quantity` -> generate names with random race
        `!namegen`  `quantity` -> generate names with random race and gender

        race:
        > the one of the available race libraries.

        gender:
        > m (male), f (female), b or blank (both/random)

        quantity:
        > number of names to generate (up to 100)
        """
        files = [f[:-3] for f in os.listdir(self.script_dir) if f.endswith(".js")]

        if not args:
            available_races = ", ".join(sorted(files))
            await ctx.send(
                "⚠️ You're missing a required argument for this command.\n\nProvide at least one of the follwoing:\n race, gender (m | f | b), or quantity.\n\n"
                f"**Available races:**\n```{available_races}```"
            )
            if hasattr(self.bot, "logger"):
                self.bot.logger.error("No arguments provided for namegen. Listed available races.")
            return

        race = None
        gender = "b"
        quantity = 1

        for arg in args:
            arg = arg.lower().strip()
            if arg.isdigit():
                quantity = int(arg)
            elif arg in ("m", "f", "b"):
                gender = arg
            elif arg in files:
                race = arg

        if quantity < 1 or quantity > 100:
            await ctx.send("❌ Quantity must be between 1 and 100.")
            return

        results = []

        for _ in range(quantity):
            selected_gender = gender
            if gender in ("", "b"):
                selected_gender = random.choice(["m", "f"])

            selected_race = race or random.choice(files)
            js_file = os.path.join(self.script_dir, f"{selected_race}.js")

            if not os.path.isfile(js_file):
                await ctx.send(f"❌ Could not find script for race: {selected_race}.")
                return

            try:
                js_file_path_for_node = js_file.replace('\\', '/')
                output = subprocess.check_output([
                    "node", js_file_path_for_node, selected_gender
                ], stderr=subprocess.STDOUT, text=True)

                full_output = output.strip()

                if "###" in full_output:
                    name_part, subrace = full_output.split("###")
                    name_part = name_part.strip()
                    subrace = subrace.strip() or "None"
                else:
                    name_part = full_output
                    subrace = "None"

                if race is None:
                    result_line = f"{name_part} [{selected_race}]"
                else:
                    result_line = f"{name_part}"

                results.append(result_line)

                if hasattr(self.bot, "logger"):
                    self.bot.logger.info(f"{result_line} [{selected_race.title()} - {subrace}]")

            except subprocess.CalledProcessError as e:
                await ctx.send(f"❌ Error generating names: {e.output}")
                return

        result_str = "\n".join(results)
        if len(result_str) > 1900:
            await ctx.send("Generated names are too long to display. Try a smaller quantity.")
        else:
            if race is None:
                await ctx.send(f"**Generated {quantity} Random Name(s):**\n```{result_str}```")
            else:
                await ctx.send(f"**Generated {quantity} {race.title()} Name(s):**\n```{result_str}```")

async def setup(bot):
    await bot.add_cog(NameGen(bot))
