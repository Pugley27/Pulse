import discord
from discord.ext import commands
import random
import re
import datetime
import asyncio

# --- Configuration ---
TOKEN = 'YOUR_BOT_TOKEN'
COMMAND_PREFIX = '!'
ADMIN_IDS = [] 

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True
intents.direct_messages = True # REQUIRED for silent bids
# Note: You may need to enable 'Direct Messages' in your Bot settings on the Portal

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Global dictionary to track the active auction
# Format: {'item': 'Valorous Cape', 'bids': {user_id: amount}, 'active': False}
auction_data = {'item': None, 'bids': {}, 'active': False}

# --- Events ---
@bot.event
async def on_ready():
    print(f'Loot Master {bot.user.name} is online.')

# --- Commands ---

@bot.command(name='startauction', help='Starts a silent auction. Usage: !startauction [Item Name]')
@commands.has_permissions(manage_messages=True)
async def start_auction(ctx, *, item_name: str):
    if auction_data['active']:
        await ctx.send("An auction is already in progress!")
        return

    auction_data['active'] = True
    auction_data['item'] = item_name
    auction_data['bids'] = {}

    await ctx.send(
        f"⚔️ **SILENT AUCTION STARTED: {item_name.upper()}** ⚔️\n"
        f"To bid, send a **Direct Message** to this bot with: `!bid [amount]`\n"
        f"The auction ends in **60 seconds**!"
    )

    await asyncio.sleep(60) # Wait for bids
    await resolve_auction(ctx)

@bot.command(name='bid', help='DM the bot this command to bid Cruor.')
async def place_bid(ctx, amount: int):
    # Check if this is a DM
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        await ctx.author.send("Bids must be sent via DM to keep them silent! I deleted your public message.")
        return

    if not auction_data['active']:
        await ctx.send("There is no active auction right now.")
        return

    if amount <= 0:
        await ctx.send("Bid must be a positive amount of Cruor.")
        return

    auction_data['bids'][ctx.author.id] = amount
    await ctx.send(f"✅ Your bid of **{amount} Cruor** for **{auction_data['item']}** has been recorded.")

async def resolve_auction(ctx):
    auction_data['active'] = False
    item = auction_data['item']
    bids = auction_data['bids']

    if not bids:
        await ctx.send(f"The auction for **{item}** ended with no bids.")
        return

    # 1. Find the highest bid amount
    max_bid = max(bids.values())
    
    # 2. Find all users who bid that amount
    winners = [user_id for user_id, amt in bids.items() if amt == max_bid]
    
    await ctx.send(f"🛑 **Auction for {item} has ended!**\n"
                   f"The highest bid was **{max_bid} Cruor**.")

    if len(winners) == 1:
        winner_user = await bot.fetch_user(winners[0])
        await ctx.send(f"🏆 **WINNER:** {winner_user.mention} with a bid of {max_bid} Cruor!")
    else:
        # 3. Tie! Start Roll-off
        candidate_mentions = " ".join([(await bot.fetch_user(uid)).mention for uid in winners])
        await ctx.send(f"🤝 **TIE DETECTED!** {candidate_mentions}, you bid the same amount. Starting the automated roll-off...")
        
        final_winner_id = await perform_roll_off(ctx, winners)
        winner_user = await bot.fetch_user(final_winner_id)
        await ctx.send(f"🎊 After the roll-off, {winner_user.mention} wins the **{item}**!")

async def perform_roll_off(ctx, user_ids):
    """Recursive/Looping roll-off logic to handle ties indefinitely."""
    while True:
        rolls = {}
        roll_results_text = "**Roll-off Results:**\n"
        
        for uid in user_ids:
            user = await bot.fetch_user(uid)
            roll = random.randint(1, 100)
            rolls[uid] = roll
            roll_results_text += f"{user.display_name}: {roll}\n"
        
        await ctx.send(roll_results_text)
        
        max_roll = max(rolls.values())
        top_rollers = [uid for uid, val in rolls.items() if val == max_roll]
        
        if len(top_rollers) == 1:
            return top_rollers[0]
        else:
            user_ids = top_rollers # Only the people who tied for high roll go to next round
            await ctx.send("♻️ **Another tie!** Rolling again for the top rollers...")
            await asyncio.sleep(2) # Short pause for dramatic effect

# --- Run the Bot ---
bot.run(TOKEN)