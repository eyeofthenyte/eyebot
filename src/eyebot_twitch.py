import datetime
import logging
from os import path
import random
import yaml

from twitchio.ext import commands
from services.configService import ConfigService
from services.logService import LogService

#Time Stamp Generation For Console Logging
def t():
    format = "%Y/%m/%d %H:%M:%S"
    now = datetime.datetime.now()
    t = now.strftime(format)
    return t

config = ConfigService(path.dirname(__file__) + "/../config.yaml").get()
logger = LogService("twitch", config["logging"])

BOT_PREFIX = "!"
if config["prefix"]:
    BOT_PREFIX = config["prefix"]

TMI_TOKEN = config["twitch"]["tmi_token"]
CLIENT_ID = config["twitch"]["client_id"]
BOT_NICK = config["twitch"]["nick"]
CHANNELS = config["twitch"]["channels"]

bot = commands.Bot(
    # set up the bot
    token = TMI_TOKEN,
    client_id = CLIENT_ID,
    nick = BOT_NICK,
    prefix = BOT_PREFIX,
    initial_channels = CHANNELS
)

bot.logger = logger
bot.config = config

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
        logger.info(f'Logged in as | %s', self.nick)
        logger.info(f'User id is | %s', self.user_id)
        logger.info(f'%s is alive', BOT_NICK)

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
            logger.info(f'%s has sought guidance.', ctx.author.name)
        await ctx.send(random.choice(replies))

bot = Bot()
bot.run()
