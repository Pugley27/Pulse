from enum import member

import discord
from discord.ext import commands
import random
import re
import datetime
from api_client import GuildAPI
import discord_bot
from dotenv import load_dotenv, version
import os
  

LOOT_ROLL_EMOJI = '🎲' # You can use any emoji, e.g., '✅', '⚔️'
with open("version.txt", "r") as file:
    version = file.read().strip()

# Load variables from .env into the system environment
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') # Set this in Railway Variables
db = discord_bot.DiscordBot(DISCORD_TOKEN)
bot = db.bot # Get the actual bot instance to use for commands and events

# Create an instance of your API client
API_KEY = os.getenv("SECRET_API_KEY") # Set this in Railway Variables
API_URL = os.getenv("API_URL")
TREASURER_ROLE_ID = int(os.getenv("TREASURER_ROLE_ID")) # Replace with your actual Role ID
ADJUDICATOR_ROLE_ID = int(os.getenv("ADJUDICATOR_ROLE_ID")) # Replace with your actual Role ID

api = GuildAPI(API_URL, API_KEY)

# --- Helper Functions ---
def parse_dice_roll(roll_str):
    """
    Parses a dice roll string (e.g., '2d6', 'd20+5') into components.
    Returns (num_dice, die_type, modifier) or None if invalid.
    """
    match = re.match(r'(\d*)d(\d+)([+\-]\d+)?', roll_str.lower())
    if match:
        num_dice_str, die_type_str, modifier_str = match.groups()
        num_dice = int(num_dice_str) if num_dice_str else 1
        die_type = int(die_type_str)
        modifier = int(modifier_str) if modifier_str else 0
        return num_dice, die_type, modifier
    return None

# --- Events ---
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id} Version: {version}')
    print(f'Command Prefix: {bot.command_prefix}')
    print('Let us choose violence!')

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

# --- Commands ---

@bot.command(name="add_cruor", description="Pay a member Cruor")
@commands.has_any_role(TREASURER_ROLE_ID, ADJUDICATOR_ROLE_ID) # Checks for the specific role
async def pay_member(ctx, member: discord.Member, amount: int):
    await ctx.defer()
    # Call a completely different function
    result = await api.update_cruor(member.id, member.display_name ,amount)
    await ctx.send(f"Added {amount} Cruor to {member.display_name} blood for the blood gods!")

@bot.command(name="get_balance", description="Check a member's Cruor balance")
async def get_balance(ctx, member: discord.Member):
    target = member or ctx.author
    response = await api.get_balance(target.id)
    
    data = response
    await ctx.send(f"💰 {target.display_name} has **{data['balance']} Cruor**.")

@bot.command(name="add_item", description="Add an item to the auction")
@commands.has_any_role(TREASURER_ROLE_ID, ADJUDICATOR_ROLE_ID) # Checks for the specific role
async def add_item(ctx, name: str, description: str):
    response = await api.add_item(name, description)
    await ctx.send(f"{name} added to the auction items with ID: {response['item_id']}")

@bot.command(name='roll', help=f'Rolls dice. Usage: {bot.command_prefix}roll [NdM][+/-X] (e.g., d20, 2d6+3)')
async def roll_dice(ctx, *, roll_string: str):
    """
    Rolls dice based on the provided string.
    """
    parsed_roll = parse_dice_roll(roll_string)
    if not parsed_roll:
        await ctx.send(f"Invalid roll format. Please use `NdM` or `NdM+/-X` (e.g., `!roll d20`, `!roll 2d6+3`).")
        return

    num_dice, die_type, modifier = parsed_roll

    if num_dice <= 0 or die_type <= 0:
        await ctx.send("Number of dice and die type must be positive integers.")
        return
    if num_dice > 100:
        await ctx.send("You can roll a maximum of 100 dice at once.")
        return
    if die_type > 1000:
        await ctx.send("The maximum die type is d1000.")
        return

    rolls = [random.randint(1, die_type) for _ in range(num_dice)]
    total = sum(rolls) + modifier

    roll_details = f"Rolls: {', '.join(map(str, rolls))}"
    if modifier != 0:
        roll_details += f" {'' if modifier < 0 else '+'}{modifier}"

    await ctx.send(f"{ctx.author.mention} rolled `{roll_string}`:\n{roll_details}\n**Total: {total}**")

@bot.command(name='lootroll', help=f'Starts a loot roll. React with {LOOT_ROLL_EMOJI} to participate and get a d100 roll.')
@commands.has_role(TREASURER_ROLE_ID) # Checks for the specific role
async def loot_roll(ctx):
    """
    Starts a loot roll where users react to participate.
    """
    message = await ctx.send(
        f"{ctx.author.mention} has initiated a **Loot Roll (d100)**! "
        f"React with the {LOOT_ROLL_EMOJI} emoji within 60 seconds to participate."
    )
    await message.add_reaction(LOOT_ROLL_EMOJI)

    await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=60))

    # Fetch the updated message to get all reactions
    message = await ctx.channel.fetch_message(message.id)
    participants = {} # User ID: Roll Result

    for reaction in message.reactions:
        if str(reaction.emoji) == LOOT_ROLL_EMOJI:
            # Iterate through reactors. Limit to 100 to prevent rate limits for very large servers.
            # In a real scenario, you might want to fetch members in chunks or use a database.
            async for user in reaction.users(limit=100):
                if user.bot:
                    continue # Don't count bot's own reaction

                if user.id not in participants:
                    participants[user.id] = random.randint(1, 100) # Roll a d100

    if not participants:
        await ctx.send("No one participated in the loot roll.")
        return

    # Sort participants by roll result, highest first
    sorted_participants = sorted(participants.items(), key=lambda item: item[1], reverse=True)

    results_message = "**Loot Roll Results:**\n"
    for user_id, roll in sorted_participants:
        user = bot.get_user(user_id) # Try to get user from cache
        if user is None:
            try:
                user = await bot.fetch_user(user_id) # Fetch user if not in cache
            except discord.NotFound:
                user = None # User left the server or is otherwise unreachable
       
        user_name = user.display_name if user else f"User ID: {user_id}"
        results_message += f"**{user_name}**: rolled **{roll}**\n"

    await ctx.send(results_message)


@bot.command(name='clear', help=f'Clears a specified number of messages. Admin only. Usage: {bot.command_prefix}clear [number]')
@commands.has_permissions(manage_messages=True)
@commands.is_owner() # This decorator makes sure only the bot owner can use it.
                      # If you want specific admins, use check_admin_permission decorator below.
async def clear_messages(ctx, count: int):
    """
    Clears the specified number of messages from the current channel.
    Requires 'Manage Messages' permission.
    """
    if ctx.author.id not in bot.admin_ids: # Custom admin check
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

# Example of using the custom admin check instead of @commands.is_owner()
# @bot.command(name='adminonly', help='An example command for admins.')
# @is_admin()
# async def admin_only_command(ctx):
#     await ctx.send("You're an admin!")

# --- Run the Bot ---
if __name__ == "__main__":
    db.run()


 
