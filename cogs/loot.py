import eyebot_discord
import os, datetime
import random
from discord.ext import commands

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

#Pass Bot Prefix
def get_prefix():
    data = open(os.path.join(os.path.dirname(__file__), "../eyebot.cfg")).read().splitlines()
    prefix = data[1]
    return prefix
    data.close()

prefix = get_prefix()

# ---------------------------------------------------------
# Random Loot Generator
# ---------------------------------------------------------
class Loot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{t()}: Looking for loose change.")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            print(f'{t()}: missing or invalid argument for .loot')
            await ctx.send('Please choose which single loot table you wish to pick loot from by typing:\n`{prefix}loot (1/2/3/4)`.\nPlease try `{prefix}loot ?` for more information.')


    #----------------------------
    # Loot Command
    #----------------------------
    @commands.command()
    async def loot(self, ctx, *, select):

        # Variables
        m_Response = ''
        d100_roll = random.randrange(1,101)
        list = [None] * 2

        # Loot Table 1
        if select == '1':
            if d100_roll < 31:
                list[0] = str(random.randrange(6,31)) + ' CP'
            elif ((d100_roll < 61) and (d100_roll > 30)):
                list[0] = str(random.randrange(4,25)) + ' SP'
            elif ((d100_roll < 71) and (d100_roll > 60)):
                list[0] = str(random.randrange(3,19)) + ' EP'
            elif ((d100_roll < 96) and (d100_roll > 70)):
                list[0] = str(random.randrange(3,19)) + ' GP'
            elif ((d100_roll <= 100) and (d100_roll > 95)):
                list[0] = str(random.randrange(1,7)) + ' PP'
            else:
                list[0] = 'There was an error.'
            m_Response = "At the end of your job you find... \n" + list[0] + "."
            embed = eyebot_discord.Embed(color=0xffe449)
            embed.set_author(name='Indivdual Treasure', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/coin_1fa99.png')
            embed.add_field(name='**__Challange 0 - 4__**', value=f'{m_Response}', inline=False)

        # Loot Table 2
        elif select == '2':
            if d100_roll < 31:
                list[0] = str(random.randrange(4,24)*100) + ' CP'
                list[1] = str(random.randrange(1,6)*10) + ' EP'
            elif ((d100_roll < 61) and (d100_roll > 30)):
                list[0] = str(random.randrange(6,36)*10) + ' SP'
                list[1] = str(random.randrange(2,12)*10) + ' GP'
            elif ((d100_roll < 71) and (d100_roll > 60)):
                list[0] = str(random.randrange(3,18)*10) + ' EP'
                list[1] = str(random.randrange(2,12)*10) + ' GP'
            elif ((d100_roll < 96) and (d100_roll > 70)):
                list[0] = str(random.randrange(4,24)*10) + ' GP'
            elif ((d100_roll <= 100) and (d100_roll > 95)):
                list[0] = str(random.randrange(2,12)*10) + ' GP'
                list[1] = str(random.randrange(3,18)) + ' PP'
            else:
                list[0] = 'There was an error.'

            m_Response = "At the end of your job you find...\n" + list[0] + '\n' + list[1]
            embed = eyebot_discord.Embed(color=0xffe449)
            embed.set_author(name='Indivdual Treasure', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/coin_1fa99.png')
            embed.add_field(name='**__Challange 5 - 10__**', value=f'{m_Response}', inline=False)

        # Loot Table 3
        elif select == '3':
            if d100_roll < 21:
                list[0] = str(random.randrange(4,24)*100) + ' SP'
                list[1] = str(random.randrange(1,6)*100) + ' GP'
            elif ((d100_roll < 36) and (d100_roll > 20)):
                list[0] = str(random.randrange(1,6)*100) + ' EP'
                list[1] = str(random.randrange(1,6)*100) + ' GP'
            elif ((d100_roll < 76) and (d100_roll > 35)):
                list[0] = str(random.randrange(2,12)*100) + ' GP'
                list[1] = str(random.randrange(1,6)*10) + ' PP'
            elif ((d100_roll <= 100) and (d100_roll > 75)):
                list[0] = str(random.randrange(2,12)*100) + ' GP'
                list[1] = str(random.randrange(2,12)*10) + ' PP'
            else:
                list[0] = 'There was an error.'
            m_Response = "At the end of your job you find...\n" + list[0] + '\n' + list[1]
            embed = eyebot_discord.Embed(color=0xffe449)
            embed.set_author(name='Indivdual Treasure', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/coin_1fa99.png')
            embed.add_field(name='**__Challange 11 - 16__**', value=f'{m_Response}', inline=False)

        # Loot Table 4
        elif select == '4':
            if d100_roll < 16:
                list[0] = str(random.randrange(2,12)*1000) + ' EP'
                list[1] = str(random.randrange(8,48)*100) + ' GP'
            elif ((d100_roll < 56) and (d100_roll > 15)):
                list[0] = str(random.randrange(1,6)*1000) + ' GP'
                list[1] = str(random.randrange(1,6)*100) + ' PP'
            elif ((d100_roll <= 100) and (d100_roll > 55)):
                list[0] = str(random.randrange(1,6)*1000) + ' GP'
                list[1] = str(random.randrange(2,12)*100) + ' PP'
            else:
                list[0] = 'There was an error.'
            m_Response = "At the end of your job you find...\n" + list[0] + '\n' + list[1]
            embed = eyebot_discord.Embed(color=0xffe449)
            embed.set_author(name='Indivdual Treasure', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/coin_1fa99.png')
            embed.add_field(name='**__Challange 17+__**', value=f'{m_Response}', inline=False)

        # Help Operator
        elif select == '?':
            print(f'{t()}: {ctx.message.author} asked for help with Loot.')
            embed = eyebot_discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Loot)', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/warning_26a0.png')
            embed.add_field(name='**__Loot__**', value='**Usage: `{prefix}loot #` where `# = 1-4`**\n Number corresponds to the 4 Individual Treasure tables in DMG - Chapter 7.\nThis will generate all coins randomly based on table selected.', inline=False)

        else:
            print(f'{t()}: {ctx.message.author} entered invalid hoard opterator')
            m_Response = "That's not a valid input. Please try again or `{prefix}loot ?` for more information."
            embed = eyebot_discord.Embed(color=0xcc0000)
            embed.set_author(name='Indivdual Treasure', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='**__Error__**', value=f'{m_Response}', inline=False)

        if eyebot_discord.ChannelType == "private":
            print(f'{t()}: {ctx.message.author} rolled for loot from table {select}.')
            await ctx.message.author.send(embed=embed)
        elif eyebot_discord.ChannelType != "private":
            print(f'{t()}: {ctx.message.author} rolled for loot from table {select}.')
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Loot(bot))
