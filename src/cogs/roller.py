import random
import re
import logging
from services.logService import LogService
from dataclasses import dataclass
from discord.ext import commands

# ---------------------------------------------------------
# Processes a Die Roll String
# ---------------------------------------------------------
@dataclass()
class Dice:
    """Represents a dice."""

    raw_quantity: str
    raw_sides: str
    raw_modifier: str
    raw_single_mod: str
    VALID_SIDES = [2, 4, 6, 8, 10, 12, 20, 100, 1000]

    def __post_init__(self):
        try:
            self.quantity = int(self.raw_quantity) if self.raw_quantity else 1
        except ValueError:
            raise ValueError(f'[{self.raw_quantity}] quantity must be a number.')
            # self.bot.logger.log(f'[{self.raw_quantity}] quantity must be a number.')

        try:
            self.sides = int(self.raw_sides)
        except ValueError:
            raise ValueError(f'[{self.raw_sides}] number of sides must be a number.')
            # self.bot.logger.log(f'[{self.raw_sides}] number of sides must be a number.')

        try:
            self.modifier = int(self.raw_modifier) if self.raw_modifier else 0
        except ValueError:
            raise ValueError(f'[{self.raw_modifier}] is not a valid modifier.')
            # self.bot.logger.log(f'[{self.raw_modifier}] is not a valid modifier.')

        try:
            self.single_mod = (int(self.raw_single_mod) if self.raw_single_mod else 0)
        except ValueError:
            raise ValueError(f'[{self.raw_single_mod}] is not a valid modifier.')
            # self.bot.logger.log(f'[{self.raw_single_mod}] is not a valid modifier.')

        if self.quantity < 1:
            raise ValueError(f'[{self.quantity}] is not a valid number of dice.')
            # self.bot.logger.log(f'[{self.quantity}] is not a valid number of dice.')

        if self.quantity > 200:
            raise ValueError(f'[{self.quantity}] that is too many dice.')
            # self.bot.logger.log(f'[{self.quantity}] that is too many dice.')

        if self.sides not in self.VALID_SIDES:
            raise ValueError(f'[{self.raw}] Allowed dice are: {self.valid_dice}.')
            # self.bot.logger.log(f'[{self.raw}] Allowed dice are: {self.valid_dice}.')

    @property
    def raw(self):
        #Return raw string of the dice
                return f'{self.raw_quantity}d{self.raw_sides}{self.raw_modifier or ""}'
                # self.bot.logger.log(f'{self.raw_quantity}d{self.raw_sides}{self.raw_modifier or ""}')

    @property
    def valid_dice(self):
        #Return string of valid dice types.
        return ', '.join(['d' + str(d) for d in self.VALID_SIDES])

    def roll(self):
        #Rolls the dice and returns a list
        rolls = []

        for i in range(self.quantity):
            dice_roll = DiceRoll(modifier=self.modifier)
            dice_roll.base = random.randint(1, self.sides)
            if self.sides == 20 and dice_roll.base == 20:
                dice_roll.crit = True
            elif self.sides == 20 and dice_roll.base == 1:
                dice_roll.fail = True
            rolls.append(dice_roll)

        return rolls


@dataclass()
class DiceRoll:
    #Represents a dice roll

    base: int = 0
    modifier: int = 0
    crit: bool = False
    fail: bool = False

    @property
    def total(self):
        #Returns the sum of the base roll value plus the modifier
        return self.base + self.modifier

    @property
    def raw(self):
        #Returns a breakdown of the roll before being totaled
        if self.modifier != 0:
            mod = f'{self.modifier:+d}'
        else:
            mod = ''
        return f'{str(self.base)}{mod}'

# ---------------------------------------------------------
# Die Roller Commands
# ---------------------------------------------------------
class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.log(f'Gathers all of the clickity-clacks.')

    DICE_PATTERN = re.compile(r"^(\d*)d(\d+)([-+]\d+)?$")

    #----------------------------
    # Check if D20 Rolls are Crit Success or Crit Fail
    #----------------------------
    @staticmethod
    def get_d20_minmax_msg(rolls):
        #Crit Fail or Crit Success Message

        msg = ''
        crit = False
        fail = False

        for roll in rolls:
            if roll.crit is True:
                crit = True
            elif roll.fail is True:
                fail = True

        if crit is True and fail is True:
            msg = (
                '\n\n  --  Natural 20 and natural 1!\n '
                'If rolling advantage, Crit!\n '
                'If rolling disadvantage, Crit Fail!'
            )
        elif crit is True:
            msg = '  --  Natural 20! (Crit)'
        elif fail is True:
            msg = '  --  Natural 1! (Crit Fail)'

        return msg


    #----------------------------
    # D20 Roller
    #----------------------------
    @commands.command()
    async def d20(self, ctx, num_dice='1'):
        #Roll one or more d20 dice.

        name = ctx.message.author.display_name

        try:
            dice = Dice(num_dice, '20', '', '')
        except ValueError as e:
            await ctx.send(f'{name} made an invalid roll: {e}')
            return

        rolls = dice.roll()

        raw_rolls = [roll.raw for roll in rolls]

        minmax_msg = self.get_d20_minmax_msg(rolls)

        if discord.ChannelType == "private":
            await ctx.message.author.send(f'{name} rolled a {dice.raw}!\nThe result was:\n{raw_rolls} {minmax_msg}')
            self.bot.logger.log(f'{name} rolled a {dice.raw}!\nThe result was:\n{raw_rolls} {minmax_msg}')
        elif discord.ChannelType != "private":
            await ctx.send(f'{name} rolled a {dice.raw}!\nThe result was:\n{raw_rolls} {minmax_msg}')
            self.bot.logger.log(f'{name} rolled a {dice.raw}!\nThe result was:\n{raw_rolls} {minmax_msg}')



    #----------------------------
    # All Die Roller
    #----------------------------
    @commands.command(aliases=['r','roll'])
    async def _roll(self, ctx, *, args=None):
        name = ctx.message.author.display_name

        if args is None:
            return

        args = args.replace(' ', '')
        results = []
        all_dice_input = []

        #self.bot.logger.log(args)

        for dice_input in re.split('[,\n]', args):
            if len(dice_input) > 0:
                all_dice_input.append(dice_input)


        for dice_input in all_dice_input:
            single_mod = ''
            if re.match('\\(.*\\)', dice_input):
                dice_input, single_mod = dice_input[1:].split(')')
                single_mod = single_mod if single_mod else ''

            try:
                dice_parts, = re.findall(self.DICE_PATTERN, dice_input)
                num, sides, mod = dice_parts
            except ValueError:
                if discord.ChannelType == "private":
                    await ctx.messege.author.send(f'{name} made an invalid roll: [{dice_input}]')
                    self.bot.logger.log(f'{name} made an invalid roll: [{dice_input}]')
                    return
                else:
                    await ctx.send(f'{name} made an invalid roll: [{dice_input}]')
                    self.bot.logger.log(f'{name} made an invalid roll: [{dice_input}]')
                    return

            try:
                dice = Dice(num, sides, mod, single_mod)
            except ValueError as e:
                if discord.ChannelType == "private":
                    await ctx.messege.autho.send(f'{name} made an invalid roll: {e}')
                    self.bot.logger.log(f'{name} made an invalid roll: {e}')
                    return
                else:
                    await ctx.send(f'{name} made an invalid roll: {e}')
                    self.bot.logger.log(f'{name} made an invalid roll: {e}')
                    return

            rolls = dice.roll()

            raw_rolls = [roll.raw for roll in rolls]
            sum_rolls = sum([roll.total for roll in rolls])

            if dice.single_mod != 0:
                result = (f'{name} rolled a {dice.raw} with a {dice.raw_single_mod} modifier!\nThe result was: {raw_rolls}\nTotal: {sum_rolls + dice.single_mod} ({sum_rolls}{dice.raw_single_mod})')
                self.bot.logger.log(f'a roll with modifier was made: {args}')
            else:
                result = (f'{name} rolled a {dice.raw}!\nThe result was: {raw_rolls}\nTotal: {sum_rolls}')
                self.bot.logger.log(f'a straight roll was made: {args}')

            result += self.get_d20_minmax_msg(rolls)

            results.append(result)

        if discord.ChannelType == "private":
            await ctx.message.author.send('\n\n'.join(results))
            self.bot.logger.log(f'Results sent to DM.')
        elif discord.ChannelType != "private":
            await ctx.send('\n\n'.join(results))
            self.bot.logger.log(f'Results sent to discord.')



async def setup(bot):
    await bot.add_cog(Roll(bot))
