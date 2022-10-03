import sys, logging
import os, json, datetime, codecs, re
import random, contextlib
from twitchio.ext import commands


#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

def read_cfg():
    lines = open(os.path.join(os.path.dirname(__file__), "eyebot.cfg")).read().splitlines()
    return lines
    lines.close()

lines = read_cfg()
TMI_TOKEN = lines[2]
BOT_PREFIX = lines[1]
CLIENT_ID = lines[3]
BOT_NICK = lines[5]
CHANNEL = lines[6]

bot = commands.Bot(
    # set up the bot
    token = TMI_TOKEN,
    client_id = CLIENT_ID,
    nick = BOT_NICK,
    prefix = BOT_PREFIX,
    initial_channels = [CHANNEL]
)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token = TMI_TOKEN,
            client_id = CLIENT_ID,
            nick = BOT_NICK,
            prefix = BOT_PREFIX,
            initial_channels = [CHANNEL]
        )

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        print(f'{BOT_NICK} is alive')

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Hello {ctx.author.name}!')


    # ---------------------------------------------------------
    # Oracle
    # ---------------------------------------------------------
    @commands.command()
    async def oracle(self, ctx, *, question):
        replies = ["Yes.", "No.", "I said NO!", "Do you really want an answer to that?", "Ask again later.", "Go play in the street.", "Shut your cock holster!","How can you even ask something like that?", "If you don't know the answer already I certainly can't help you.", "Lets be honest you could use the life experience.", "Lets just say... your best option would be to put your head between your legs and kiss your ass goodbye.", "Definitely maybe.", "Ask me again someday.", "*~Unintelligable, Yet Frightening Wispers~*","*~Disembodied Laughter of Children~*"];
        if (int(question.count(" ")) >= 2):
            print(f'{t()}: {ctx.author.name} has sought guidance.')
        await ctx.send(random.choice(replies))    

bot = Bot()
bot.run()
