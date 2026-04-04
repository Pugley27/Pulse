import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import os

class DiscordBot():
    def __init__ (self, token,  command_prefix='!', admin_ids=None):
# --- Bot Setup ---
        self.intents = discord.Intents.default()
        self.intents.message_content = True  # Enable the message content intent
        self.intents.members = True # Required for fetching members in lootroll if they aren't cached        self.token = token
        self.admin_ids = admin_ids or []
        self.command_prefix = command_prefix
        self.bot = commands.Bot(command_prefix=self.command_prefix, intents=self.intents)
        self.token = token

    def run(self):
        self.bot.run(self.token)            


