import discord
from discord.ext import commands
import os


class DiscordBot():
    def __init__ (self, token, intents,  command_prefix='!', admin_ids=None):
        self.token = token
        self.admin_ids = admin_ids or []
        self.command_prefix = command_prefix
        self.intents = intents
        self.bot = commands.Bot(command_prefix=self.command_prefix, intents=self.intents)

    def run(self):
        self.bot.run(self.token)            

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.members = True # Required for fetching members in lootroll if they aren't cached

db = DiscordBot(token=os.getenv('DISCORD_TOKEN'), intents=intents)
bot = db.bot # Get the actual bot instance to use for commands and events
