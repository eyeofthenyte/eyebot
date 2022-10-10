import os, json, datetime, codecs, re
import random, contextlib
import sys, logging
import yaml

from twitchio.ext import commands
from yaml.loader import SafeLoader

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

def read_cfg():
    with open('config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
        return data

    # default is no config
    return null

config = read_cfg()
if (!config):
    return

config = read_cfg()

BOT_PREFIX = not config.prefix ? "!" : config.prefix
TMI_TOKEN = config.twitch.tmi_token
CLIENT_ID = config.twitch.client_id
BOT_NICK = config.twitch.nick
CHANNELS = config.twitch.channels

bot = commands.Bot(
    # set up the bot
    token = TMI_TOKEN,
    client_id = CLIENT_ID,
    nick = BOT_NICK,
    prefix = BOT_PREFIX,
    initial_channels = CHANNELS
)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token = TMI_TOKEN,
            client_id = CLIENT_ID,
            nick = BOT_NICK,
            prefix = BOT_PREFIX,
            initial_channels = CHANNELS
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
