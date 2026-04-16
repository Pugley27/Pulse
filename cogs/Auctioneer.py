import asyncio
import asyncpg
from discord.ext import tasks, commands
from datetime import datetime, timezone

class Auctioneer(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool # Your asyncpg connection pool
        print("Auctioneer initialized.")    
        self.check_auctions.start()

    def cog_unload(self):
        self.check_auctions.cancel()

    @tasks.loop(seconds=15) # Check every 30 minutes
    async def check_auctions(self):
        print("Checking for expired auctions...")
        # Query for auctions that ended but are still marked active
        # We use 'FOR UPDATE' to lock rows if you have multiple bot clusters
        query = """
            SELECT id, name, item_id, end_time 
            FROM auctions
            WHERE end_time <= $1 AND status = 'active'
        """
        now = datetime.now(timezone.utc)
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                expired_auctions = await conn.fetch(query, now)

                print(f"Checked for expired auctions at {now}. Found {len(expired_auctions)} expired auctions.")
                for record in expired_auctions:
                    print(f"Processing expired auction: {record['id']} - {record['name']} (ended at {record['end_time']})")
                    await self.process_auction_end(record, conn)
                    

    @check_auctions.before_loop
    async def before_check_auctions(self):
        # This waits until the bot is fully logged in before starting the loop
        await self.bot.wait_until_ready()
        print("✅ Auction loop is starting up...")

    @check_auctions.error
    async def on_auction_error(self, error):
        # This will catch and print any DB or code errors that normally happen silently
        print(f"❌ ERROR in auction loop: {error}")

    async def process_auction_end(self, record, conn):
        channel = self.bot.get_channel(1493392989647540304)
        if not channel:
            return

        # Query your database for a random winner among the highest bidders
        winner_query = """
            SELECT user_id, amount 
            FROM bids 
            WHERE auction_id = $1 
            AND amount = (
                SELECT MAX(amount) 
                FROM bids 
                WHERE auction_id = $1
            )
            ORDER BY RANDOM() 
            LIMIT 1
        """

        winner = await conn.fetchrow(winner_query, record['id'])

        print(f"Processing auction end for {record['id']}. Winner: {winner['user_id'] if winner else 'None'}")

        if winner:

           # Loopup item name from items table
            item_query = "SELECT name FROM auction_items WHERE id = $1"
            item_record = await conn.fetchrow(item_query, record['item_id'])
            item_name = item_record['name'] if item_record else f"Item {record['item_id']}"

            # Update status so we know who won and that the auction is no longer active and remove cruor from winner
            await conn.execute("UPDATE auctions SET status = 'awarded', winner_id = $2 WHERE id = $1", record['id'], winner['user_id'])
            #update auction item status to sold
            await conn.execute("UPDATE auction_items SET status = 'sold', member_id = $2 WHERE id = $1", record['item_id'], winner['user_id'])
            # Deduct the bid amount from the winner's balance in the lootBox table
            await conn.execute(
                'UPDATE "lockBox" SET cruor_amount = cruor_amount - $1 WHERE member_id = $2',
                winner['amount'], winner['user_id']
            )

            # Send a message to the channel announcing the winner
            await channel.send(
                f"🏆 **Auction Ended!**\n"
                f"Item #{record['id']}: **{item_name}**\n"
                f"Winner: <@{winner['user_id']}> with a bid of {winner['amount']} Cruor!"
                )

        else:
            # No bids were placed, mark as unscheduled with no winner
            await conn.execute("UPDATE auctions SET status = 'unscheduled', winner_id = $2 WHERE id = $1", record['id'], None)
            await channel.send(f"🚫 **Auction Ended!**\nNo bids were placed for {record['id']}.")

        # remove all bids for that auction
        await conn.execute("DELETE FROM bids WHERE auction_id = $1", record['id'])

# This function is required for main.py to load the file
async def setup(bot):
    await bot.add_cog(Auctioneer(bot, bot.db_pool))
