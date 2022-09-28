import sys, discord
import os, json, datetime, codecs, re
import random, contextlib
from discord.ext import commands, tasks
from discord import Activity, ActivityType
from discord.utils import find
from eyebot import t


# ---------------------------------------------------------
# Loot Hoard Generator
# ---------------------------------------------------------
class Hoard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    #----------------------------
    # Events
    #----------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{t()}: Swimming through the treasure.')
    
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            print(f'{t()}: missing or invalid argument for .hoard')
            await ctx.send('Please choose which hoard loot table you wish to pick loot from by typing:\n`!hoard (1/2/3/4)`.\nPlease try `.hoard ?` for more information.')
    
    
    #----------------------------
    # Hoard Loot Generator
    #----------------------------
    @commands.command()
    async def hoard(self, ctx, select):
        #----------------------------
        # Variables
        #----------------------------
        m_Response = ''
        m2_Response = []
        m3_Response = []
        m_Magic = [''] * 2
        randline = ''
        coins = ''
        magic = ''
        magic2 = ''
        count = 0
        count2 = 0
        mlist = [''] * 2
    
        #----------------------------
        # Hoard Loot Table 1
        #----------------------------
        if select == '1': 
            coins = str(random.randrange(6,37)*100) + ' x CP\n' + str(random.randrange(3,19)*100) + ' x SP\n' + str(random.randrange(2,13)*10) + ' x GP\n'
            lines = open(os.path.join(os.path.dirname(__file__), './hoard/hoard1.txt')).read().splitlines()
            randline = random.choice(lines)
            list = randline.split(';')
            if list[0] == '1':
                list[0] = str(random.randrange(2,13))
            elif list[0] == '2':
                list[0] = str(random.randrange(2,9))
            elif list[0] == '3':
                list[0] = str(random.randrange(2,13))
            else:
                list[0] = ''
            if list[2] == '9':
                list[2] = str(random.randrange(1,7))
            elif list[2] == '8':
                list[2] = str(random.randrange(1,5))
            elif list[2] == '1':
                list[2] = '1'
            else:
                list[2] = ''
            m_Response = f'__In the final loot hoard you find...__\n{coins} {list[0]} {list[1]} {list[2]} {list[3]} {list[4]}.'
            
            # Magic item list generation
            if list[2] != '':
                m_Magic[0] = f'\n__You find the following magical :sparkles: item(s)__:\n'
                m2_Response = [''] * int(list[2])
                for i in range(int(list[2])):
                    mlines = open(os.path.join(os.path.dirname(__file__), './hoard/magictable'+list[4]+'.txt')).read().splitlines()
                    magic = random.choice(mlines)
                    mlist = magic.split(';')
                    if mlist[1] == '1':
                        figure = open(os.path.join(os.path.dirname(__file__), './hoard/figurine.txt')).read().splitlines()
                        power = random.choice(figure)
                        mlist[0] = power
                    elif mlist[1] == '2':
                        magical = open(os.path.join(os.path.dirname(__file__), './hoard/magicarmor.txt')).read().splitlines()
                        armor = random.choice(magical)
                        mlist[0] = armor
                    else:
                        mlist[0] = mlist[0]
                    m2_Response[i] = mlist[0]
    
            embed = discord.Embed(color=0xffe449)
            embed.set_author(name='Treasure Hoard', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/money-bag_1f4b0.png')
            embed.add_field(name='**__Challange 0 - 4__**', value = str(m_Response).replace("and","\n") + '\n' + m_Magic[0] + str(m2_Response).replace("'","").replace("[","").replace("]","").replace(",","\n"), inline=False)


        #----------------------------
        # Hoard Loot Table 2
        #----------------------------
        elif select == '2':
            coins = str(random.randrange(2,13)*100) + ' x CP\n' + str(random.randrange(2,13)*1000) + ' x SP\n' + str(random.randrange(6,37)*100) + ' x GP\n' + str(random.randrange(3,19)*10) + ' x PP\n'
            lines = open(os.path.join(os.path.dirname(__file__), './hoard/hoard2.txt')).read().splitlines()
            randline = random.choice(lines)
            list = randline.split(';')
            if list[0] == '1':
                list[0] = str(random.randrange(2,9))
            elif list[0] == '2':
                list[0] = str(random.randrange(3,19))
            else:
                list[0] = ''
            if list[2] == '9':
                list[2] = str(random.randrange(1,7))
            elif list[2] == '8':
                list[2] = str(random.randrange(1,5))
            elif list[2] == '1':
                list[2] = '1'
            else:
                list[2] = ''
            m_Response = f'__In the final loot hoard you find...__\n{coins} {list[0]} {list[1]} {list[2]} {list[3]} {list[4]}.'
    
            # Magic item list generation
            if list[2] != '':
                m_Magic[0] = f'\n__You find the following magical :sparkles: item(s)__:\n'
                m2_Response = [''] * int(list[2])
                for i in range(int(list[2])):
                    mlines = open(os.path.join(os.path.dirname(__file__), './hoard/magictable'+list[4]+'.txt')).read().splitlines()
                    magic = random.choice(mlines)
                    mlist = magic.split(';')
                    if mlist[1] == '1':
                        figure = open(os.path.join(os.path.dirname(__file__), './hoard/figurine.txt')).read().splitlines()
                        power = random.choice(figure)
                        mlist[0] = power
                    elif mlist[1] == '2':
                        magical = open(os.path.join(os.path.dirname(__file__), './hoard/magicarmor.txt')).read().splitlines()
                        armor = random.choice(magical)
                        mlist[0] = armor
                    else:
                        mlist[0] = mlist[0]
                    m2_Response[i] = mlist[0]
    
            embed = discord.Embed(color=0xffe449)
            embed.set_author(name='Treasure Hoard', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/money-bag_1f4b0.png')
            embed.add_field(name='**__Challange 5 - 10__**', value = str(m_Response).replace("and","\n") + '\n' + m_Magic[0] + str(m2_Response).replace("'","").replace("[","").replace("]","").replace(",","\n"), inline=False)


        #----------------------------
        # Hoard Loot Table 3
        #----------------------------
        elif select == '3':
            coins = str(random.randrange(4,25)*1000) + ' x GP\n' + str(random.randrange(5,31)*100) + ' x PP\n'
            lines = open(os.path.join(os.path.dirname(__file__), './hoard/hoard3.txt')).read().splitlines()
            randline = random.choice(lines)
            list = randline.split(';')
            if list[0] == '1':
                list[0] = str(random.randrange(2,9))
            elif list[0] == '2':
                list[0] = str(random.randrange(3,19))
            else:
                list[0] = ''
            if list[2] == '9':
                list[2] = str(random.randrange(1,7))
            elif list[2] == '8':
                list[2] = str(random.randrange(1,5))
            elif list[2] == '1':
                list[2] = '1'
            else:
                list[2] = ''
            if list[6] == '8':
                list[6] = str(random.randrange(1,5))
            elif list[6]== '9':
                list[6] = str(random.randrange(1,7))
            else:
                list[6] = ''
            m_Response = f'__In the final loot hoard you find...__\n{coins} {list[0]} {list[1]} {list[2]} {list[3]} {list[4]} {list[5]} {list[6]} {list[7]} {list[8]}.'
    
            # Magic item list generation
            if list[2] != '':
                m_Magic[0] = f'\n__You find the following magical :sparkles: item(s)__:\n'
                m2_Response = [''] * int(list[2])
                for i in range(int(list[2])):
                    mlines = open(os.path.join(os.path.dirname(__file__), './hoard/magictable' + list[4] +'.txt')).read().splitlines()
                    magic = random.choice(mlines)
                    mlist = magic.split(';')
                    if mlist[1] == '1':
                        figure = open(os.path.join(os.path.dirname(__file__), './hoard/figurine.txt')).read().splitlines()
                        power = random.choice(figure)
                        mlist[0] = power
                    elif mlist[1] == '2':
                        magical = open(os.path.join(os.path.dirname(__file__), './hoard/magicarmor.txt')).read().splitlines()
                        armor = random.choice(magical)
                        mlist[0] = armor
                    else:
                        mitem = mlist[0]
                    m2_Response[i] = mitem
                    mlist = [''] * 2

            if list[6] != '':
                m_Magic[1] = '\nand \n'
                m3_Response = [''] * int(list[6])
                for i in range(int(list[6])):
                    mlines2 = open(os.path.join(os.path.dirname(__file__), './hoard/magictable'+list[8]+'.txt')).read().splitlines()
                    magic2 = random.choice(mlines2)
                    mlist2 = magic2.split(';')
                    if mlist2[1] == '1':
                        figure = open(os.path.join(os.path.dirname(__file__), './hoard/figurine.txt')).read().splitlines()
                        power = random.choice(figure)
                        mlist2[0] = power
                    elif mlist2[1] == '2':
                        magical = open(os.path.join(os.path.dirname(__file__), './hoard/magicarmor.txt')).read().splitlines()
                        armor = random.choice(magical)
                        mlist2[0] = armor
                    else:
                        mlist2[0] = mlist2[0]
                    m3_Response[i] = mlist2[0]
            embed = discord.Embed(color=0xffe449)
            embed.set_author(name='Treasure Hoard', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/money-bag_1f4b0.png')
            embed.add_field(name='**__Challange 11 - 16__**', value = str(m_Response).replace("and","\n") + '\n' + m_Magic[0] + str(m2_Response).replace("'","").replace("[","").replace("]","").replace(",","\n") + m_Magic[1] + str(m3_Response).replace("'","").replace("[","").replace("]","").replace(",","\n"), inline=False)

    
        #----------------------------
        # Hoard Loot Table 4
        #----------------------------
        elif select == '4':
            coins = str(random.randrange(12,73)*1000) + ' x GP\n' + str(random.randrange(8,49)*1000) + ' x PP\n'
            lines = open(os.path.join(os.path.dirname(__file__), './hoard/hoard4.txt')).read().splitlines()
            randline = random.choice(lines)
            list = randline.split(';')
            if list[0] == '1':
                list[0] = str(random.randrange(3,19))
            elif list[0] == '2':
                list[0] = str(random.randrange(1,11))
            elif list[0] == '3':
                list[0] = str(random.randrange(1,4))
            elif list[0] == '5':
                list[0] = str(random.randrange(1,8))
            else:
                list[0] = ''
            if list[2] == '9':
                list[2] = str(random.randrange(1,7))
            elif list[2] == '8':
                list[2] = str(random.randrange(1,5))
            elif list[2] == '7':
                list[2] = str(random.randrange(1,9))
            else:
                list[2] = ''
            m_Response = f'__In the final loot hoard you find...__\n{coins} {list[0]} {list[1]} {list[2]} {list[3]} {list[4]}.'
    
        # Magic item list generation
            if list[2] != '':
                m_Magic[0] = f'\n__You find the following magical :sparkles: item(s)__:\n'
                m2_Response = [''] * int(list[2])
                for i in range(int(list[2])):
                    mlines = open(os.path.join(os.path.dirname(__file__), './hoard/magictable'+list[4]+'.txt')).read().splitlines()
                    magic = random.choice(mlines)
                    mlist = magic.split(';')
                    if mlist[1] == '1':
                        figure = open(os.path.join(os.path.dirname(__file__), './hoard/figurine.txt')).read().splitlines()
                        mlist[0] = power
                    elif mlist[1] == '2':
                        magical = open(os.path.join(os.path.dirname(__file__), './hoard/figurine.txt')).read().splitlines()
                        armor = random.choice(magical)
                        mlist[0] = armor
                    else:
                        mlist[0] = mlist[0]
                    m2_Response[i] = mlist[0]
    
                embed = discord.Embed(color=0xffe449)
                embed.set_author(name='Treasure Hoard', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/money-bag_1f4b0.png')
                embed.add_field(name='**__Challange 17+__**', value = str(m_Response).replace("and","\n") + '\n' + m_Magic[0] + str(m2_Response).replace("'","").replace("[","").replace("]","").replace(",","\n"), inline=False)


        #----------------------------
        # Help Operator
        #----------------------------
        elif select == '?':
            print(f'{t()}: {ctx.message.author}({ctx.message.author.guild}) asked for help with Hoard Loot.')
            embed = discord.Embed(color=0x019cd0)
            embed.set_author(name='Help (Hoard)', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/warning_26a0.png')
            embed.add_field(name=':moneybag:  **__Hoard__**', value='**Usage: `.hoard #` where `# = 1-4`**\n Number corresponds to the 4 Treasure Hoard tables in DMG - Chapter 7.\nThis will generate all coins and magical items randomly based on table selected.', inline=False)


        else:
            print(f'{t()}: invalid hoard opterator entered.')
            m_Response = "That's not a valid input. Please try again or `.hoard ?` for more information."
            embed = discord.Embed(color=0xcc0000)
            embed.set_author(name='Treasure Hoard', icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/prohibited_1f6ab.png')
            embed.add_field(name='**__Error__**', value=f'{m_Response}', inline=False)


        if discord.ChannelType == "private":
            if select == '1':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} * magic table(s) {list[4]}')
            elif select == '2':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} & magic table(s) {list[4]}')
            elif select == '3':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} & magic table(s) {list[4]} {list[8]}')
            elif select == '4':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} & magic table(s) {list[4]}')
            await message.author.send(embed=embed)
            return
        else:
            if select == '1':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} * magic table(s) {list[4]}')
            elif select == '2':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} & magic table(s) {list[4]}')
            elif select == '3':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} & magic table(s) {list[4]} {list[8]}')
            elif select == '4':
                print(f'{t()}: {ctx.message.author} rolled for hoard loot from table {select} & magic table(s) {list[4]}')
            await ctx.send(embed=embed)
            return

    
def setup(bot):
    bot.add_cog(Hoard(bot))
