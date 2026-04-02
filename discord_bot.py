import discord
from discord.ext import commands

class DiscordBot():
    def __init__ (self, token, intents,  command_prefix='!', admin_ids=None):
        self.token = token
        self.admin_ids = admin_ids or []
        self.bot.command_prefix = command_prefix
        self.intents = intents
        self.bot = commands.Bot(command_prefix=self.command_prefix, intents=self.intents)

    def run(self):
        self.bot.run(self.token)            



