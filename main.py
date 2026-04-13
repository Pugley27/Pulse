import asyncio
import discord
from discord.ext import commands
from api_client import GuildAPI
import config 

# This is the main file that runs the bot. It initializes the bot, loads cogs, and handles events and errors.
class MyBot(commands.Bot):
    def __init__(self):
        # Load configuration from environment variables
        self.config = config.Config() 
        
        # Set up intents (required for certain features like fetching members)
        intents = discord.Intents.default()
        intents.message_content = True  # Enable the message content intent
        intents.members = True # Required for fetching members in lootroll if they aren't cached 
        admin_ids = None

        # Initialize the bot with the command prefix and intents
        super().__init__(command_prefix=self.config.command_prefix, intents=intents)

    # This is called when the bot is ready to start. We can load cogs here.
    async def setup_hook(self):
        # Initialize the API client with the URL and key from the config
        self.api = GuildAPI(self.config.API_URL, self.config.API_KEY)

        # Load cogs (these are the command modules that handle different functionalities)
        # Load currency cog for handling Cruor balance and transactions
        await self.load_extension("cogs.Currency")  

        # Load auctions cog for handling auction-related commands
        await self.load_extension("cogs.Auctions")  
        print("Cogs loaded successfully.")

        # Syncing here makes commands available globally
        # await self.tree.sync()
        MY_GUILD = discord.Object(id=691310669181747260) 
        self.tree.copy_global_to(guild=MY_GUILD) # Copies your global commands to the guild
        await self.tree.sync(guild=MY_GUILD)
        print(f"Synced slash commands for {self.user}")


# The following code sets up event handlers for when the bot is ready and for handling command errors.
async def main():
    # Create an instance of the bot
    bot = MyBot()

    # Event handler for when the bot is ready,  TODO: Move this to a separate file if it gets too long
    @bot.event
    async def on_ready():
        print(f'{bot.user.name} has connected to Discord!')
        print(f'Bot ID: {bot.user.id} Version: {bot.config.version}')
        print(f'Command Prefix: {bot.command_prefix}')
        print('Let us choose violence!')

    # Global error handler for commands. This will catch errors that aren't handled in individual cogs. TODO: Move this to a separate file if it gets too long
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Missing arguments. Please check the `!help` command for usage.')
        elif isinstance(error, commands.CommandNotFound):
            # We can ignore this as it just means a non-command message was sent
            pass
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the necessary permissions to use this command.")
        elif isinstance(error, commands.NotOwner):
            await ctx.send("You are not authorized to use this command.")
        else:
            print(f"An error occurred: {error}")
            await ctx.send(f"An error occurred while processing your command: `{error}`") 

    # TODO:  move these admin commands to a separate cog if we add more of them. For now, this is the only admin command so it can stay here.
    @bot.command(name='clear', help=f'Clears a specified number of messages. Admin only. Usage: {bot.command_prefix}clear [number]')
    @commands.has_permissions(manage_messages=True)
    @commands.is_owner() # This decorator makes sure only the bot owner can use it.
    async def clear_messages(ctx, count: int):
        """
        Clears the specified number of messages from the current channel.
        Requires 'Manage Messages' permission.
        """
        #if ctx.author.id not in bot.admin_ids: # Custom admin check
        if not await bot.is_owner(ctx.author): # Also check if the author is the bot's owner
            await ctx.send("You are not authorized to use this command.")
            return

        if count <= 0:
            await ctx.send("Please provide a positive number of messages to clear.")
            return

        # Add 1 to count to include the command message itself
        deleted = await ctx.channel.purge(limit=count + 1)
        await ctx.send(f"Cleared {len(deleted) - 1} messages.", delete_after=5) # -1 to not count the command itself

    # Custom check for bot.admin_ids (if you don't want to use commands.is_owner)
    def is_admin():
        async def predicate(ctx):
            if ctx.author.id in bot.admin_ids:
                return True
            # Fallback to check if the user is the bot's owner
            return await ctx.bot.is_owner(ctx.author)
        return commands.check(predicate)

    # Start the bot
    async with bot:
        await bot.start(bot.config.TOKEN)            

# --- Run the Bot ---
if __name__ == "__main__":
    asyncio.run(main())
