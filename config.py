import os
from discord import file
from dotenv import load_dotenv


# This file handles loading configuration from environment variables. It uses the `dotenv` library to load variables from a .env file, 
# and then makes them available as attributes of the `Config` class.
#  This allows us to easily access configuration values throughout our bot without hardcoding them in multiple places.
class Config:

    # The __init__ method is called when an instance of the Config class is created. It loads the environment variables and sets up the configuration attributes.
    def __init__(self):
        load_dotenv()    

        # Command Prefix for the bot, e.g., "!" or "?"
        self.command_prefix = os.getenv("COMMAND_PREFIX", "!")

        # Discord Bot Token, required for the bot to connect to Discord. Set this in your .env file.
        self.TOKEN = os.getenv("DISCORD_TOKEN")

        # API Key and URL for interacting with your backend API. Set these in your .env file.
        self.API_KEY = os.getenv("SECRET_API_KEY") # Set this in Railway Variables
        self.API_URL = os.getenv("API_URL")

        # Role IDs for staff roles. Set these in your .env file. These are used for permission checks in commands.
        self.TREASURER_ROLE_ID = int(os.getenv("TREASURER_ROLE_ID")) # Replace with your actual Role ID
        self.ADJUDICATOR_ROLE_ID = int(os.getenv("ADJUDICATOR_ROLE_ID")) # Replace with your actual Role ID
        self.STAFF_ROLES = [self.TREASURER_ROLE_ID, self.ADJUDICATOR_ROLE_ID]
        self.DATABASE_URL = os.getenv("DATABASE_URL") # Set this in your .env file, e.g., postgresql://user:password@host:port/database 
        
        #Set the guild ID for syncing commands. This should be the ID of your testing server or main server where you want the commands to be available.
        self.GUILD_ID = int(os.getenv("GUILD_ID")) 
        
        # Set the auction channel ID where auction results will be posted. This should be the ID of the channel in your server where you want auction notifications to appear.
        self.AUCTION_CHANNEL_ID = int(os.getenv("AUCTION_CHANNEL_ID"))
        
        # TODO: Not sure if needed but kept for posterity   
        self.LOOT_ROLL_EMOJI = '🎲' # You can use any emoji, e.g., '✅', '⚔️'   

        # Load the bot version from a file. This is just for informational purposes and can be displayed in the on_ready event or in a !version command.
        with open("version.txt", "r") as file:
            self.version: str = file.read().strip()
        
