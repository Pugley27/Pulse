import discord
from discord.ext import commands
import random
import os
import psycopg2
from psycopg2 import extras
import datetime
import asyncio

# --- Configuration ---
TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL') # Provided by Railway
TREASURER_ROLE_ID = 123456789012345678 

# --- Database Connection ---
def get_db_connection():
    # Use sslmode='require' for cloud databases like Railway
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Table for Bank
    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id BIGINT PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )''')
    # Table for Auctions
    cur.execute('''
        CREATE TABLE IF NOT EXISTS auctions (
            id SERIAL PRIMARY KEY,
            item_name TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    # Table for Bids
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            auction_id INTEGER REFERENCES auctions(id),
            user_id BIGINT,
            amount INTEGER,
            PRIMARY KEY (auction_id, user_id)
        )''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.direct_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Auction Logic with Postgres ---

@bot.command(name='startauction')
@commands.has_role(TREASURER_ROLE_ID)
async def start_auction(ctx, *, item_name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ensure no other auction is active
    cur.execute("SELECT id FROM auctions WHERE status = 'active'")
    if cur.fetchone():
        await ctx.send("🚨 An auction is already running!")
        conn.close()
        return

    # Create new auction
    cur.execute("INSERT INTO auctions (item_name) VALUES (%s) RETURNING id", (item_name,))
    auction_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    await ctx.send(
        f"⚔️ **SILENT AUCTION STARTED: {item_name.upper()}** ⚔️\n"
        f"DM the bot `!bid [amount]` to enter. Auction ends in 60 seconds!"
    )

    await asyncio.sleep(60)
    await resolve_auction(ctx, auction_id)

@bot.command(name='bid')
async def place_bid(ctx, amount: int):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        await ctx.author.send("Keep it secret! Bid via DM only.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    # Get the current active auction
    cur.execute("SELECT id, item_name FROM auctions WHERE status = 'active'")
    auction = cur.fetchone()

    if not auction:
        await ctx.send("No active auction found.")
        conn.close()
        return

    auction_id, item_name = auction

    # Check balance
    cur.execute("SELECT balance FROM players WHERE user_id = %s", (ctx.author.id,))
    res = cur.fetchone()
    balance = res[0] if res else 0

    if amount > balance:
        await ctx.send(f"❌ Poor form! You only have {balance} Cruor.")
    else:
        # Upsert bid (Update if exists, Insert if not)
        cur.execute('''
            INSERT INTO bids (auction_id, user_id, amount) VALUES (%s, %s, %s)
            ON CONFLICT (auction_id, user_id) DO UPDATE SET amount = EXCLUDED.amount
        ''', (auction_id, ctx.author.id, amount))
        conn.commit()
        await ctx.send(f"✅ Bid of **{amount}** for **{item_name}** recorded!")

    cur.close()
    conn.close()

async def resolve_auction(ctx, auction_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Set status to ended
    cur.execute("UPDATE auctions SET status = 'ended' WHERE id = %s RETURNING item_name", (auction_id,))
    item_name = cur.fetchone()[0]

    # Get bids
    cur.execute("SELECT user_id, amount FROM bids WHERE auction_id = %s", (auction_id,))
    all_bids = cur.fetchall() # List of (user_id, amount)

    if not all_bids:
        await ctx.send(f"The auction for **{item_name}** ended with no bids.")
        conn.commit()
        conn.close()
        return

    max_bid = max(b[1] for b in all_bids)
    winners = [b[0] for b in all_bids if b[1] == max_bid]

    await ctx.send(f"🛑 **Auction for {item_name} has ended!** Max bid: **{max_bid} Cruor**.")

    final_winner_id = None
    if len(winners) == 1:
        final_winner_id = winners[0]
    else:
        # Re-use your perform_roll_off logic here
        await ctx.send("🤝 **TIE!** Starting automated roll-off...")
        final_winner_id = await perform_roll_off(ctx, winners)

    # Deduct Cruor
    cur.execute("UPDATE players SET balance = balance - %s WHERE user_id = %s", (max_bid, final_winner_id))
    conn.commit()
    
    winner_user = await bot.fetch_user(final_winner_id)
    await ctx.send(f"🏆 **WINNER:** {winner_user.mention} has won **{item_name}**!")
    
    cur.close()
    conn.close()

# Note: Keep your perform_roll_off, add_cruor, and balance commands from previous steps,
# just ensure they use get_db_connection() and Postgres syntax (%s instead of ?).