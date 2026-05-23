import asyncio
import asyncpg
from discord.ext import tasks, commands
from datetime import datetime, timezone

class Auctioneer(commands.Cog, ):
    def __init__(self, bot, db_pool, ):
        self.bot = bot
        self.db_pool = db_pool  # Your asyncpg connection pool
        print("Auctioneer initialized.")    
        self.check_auctions.start()
        self.channel_id = self.bot.config.AUCTION_CHANNEL_ID  # Get the channel ID from the bot's config

    def cog_unload(self):
        self.check_auctions.cancel()

    @tasks.loop(minutes=1)
    async def check_auctions(self):
        print("Checking for expired auctions...")
        query = """
            SELECT a.id, a.name, a.item_id, a.end_time, i.quantity 
            FROM auctions a
            JOIN auction_items i ON a.item_id = i.id
            WHERE a.end_time <= $1 AND a.status = 'active'
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
        await self.bot.wait_until_ready()
        print("✅ Auction loop is starting up...")

    @check_auctions.error
    async def on_auction_error(self, error):
        print(f"❌ ERROR in auction loop: {error}")

    async def process_auction_end(self, record, conn):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return

        # Fetch top unique bids matching up to the total available item quantity
        winners_query = """
            SELECT user_id, amount 
            FROM (
                SELECT user_id, amount,
                       ROW_NUMBER() OVER (ORDER BY amount DESC, created_at ASC) as rank
                FROM bids 
                WHERE auction_id = $1
            ) ranked_bids
            WHERE rank <= $2
        """

        winners = await conn.fetch(winners_query, record['id'], record['quantity'])
        actual_items_won = len(winners)

        print(f"Processing auction end for {record['id']}. Found {actual_items_won} winners out of {record['quantity']} slots.")

        if winners:
            # Fetch the current item details from the inventory catalog
            item_query = "SELECT name, description, quantity, holder_id FROM auction_items WHERE id = $1"
            item_record = await conn.fetchrow(item_query, record['item_id'])
            item_name = item_record['name'] if item_record else f"Item {record['item_id']}"

            # 1. Update overall auction state to awarded
            await conn.execute("UPDATE auctions SET status = 'awarded' WHERE id = $1", record['id'])
            
            # 2. Manage inventory clean-off / split logic
            # Calculate any remaining stock left unallocated
            leftover_quantity = record['quantity'] - actual_items_won

            if leftover_quantity > 0 and item_record:
                # Part of the batch went unsold. Clone the leftovers into a brand new available row!
                leftover_id = await conn.fetchval(
                    """
                    INSERT INTO auction_items (name, description, quantity, status, auction_id, holder_id)
                    VALUES ($1, $2, $3, 'available', NULL, $4)
                    RETURNING id;
                    """,
                    item_record['name'], item_record['description'], leftover_quantity, item_record['holder_id']
                )
                print(f"♻️ Leftovers generated: Created new item row ID {leftover_id} with {leftover_quantity} units.")
            
            # Delete the old item batch row entirely so it is completely cleaned off active tracking
            await conn.execute("DELETE FROM auction_items WHERE id = $1", record['item_id'])

            announcement_lines = [
                f"🏆 **Multi-Unit Auction Ended!**",
                f"Item: **{item_name}** (Auction #{record['id']})",
                f"Units Awarded: **{actual_items_won}** / **{record['quantity']}**\n",
                "**Winners (Items added to the Handout Queue):**"
            ]

            # 3. Insert each individual winner into the claimed_items table and deduct balances
            for index, winner in enumerate(winners, start=1):
                # Deduct currency
                await conn.execute(
                    'UPDATE "lockBox" SET cruor_amount = cruor_amount - $1 WHERE member_id = $2',
                    winner['amount'], winner['user_id']
                )
                
                # Move to the fulfillment queue table
                await conn.execute(
                    """
                    INSERT INTO claimed_items (auction_id, item_id, name, winner_id, winning_bid, claimed_at, handed_out, holder_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    record['id'], record['item_id'], item_name, winner['user_id'], winner['amount'], datetime.now(timezone.utc), False, item_record['holder_id']
                )

                announcement_lines.append(
                    f"{index}. <@{winner['user_id']}> — **{winner['amount']}** Cruor"
                )

            # Send full roster to Discord
            await channel.send("\n".join(announcement_lines))

        else:
            # No bids placed at all: reset auction status to unscheduled.
            # The item remains in auction_items completely untouched since zero quantity was removed.
            await conn.execute("UPDATE auctions SET status = 'unscheduled' WHERE id = $1", record['id'])
            await channel.send(f"🚫 **Auction Ended!**\nNo bids were placed for {record['id']}.")

        # Clear active bid records for this completed lifecycle event
        await conn.execute("DELETE FROM bids WHERE auction_id = $1", record['id'])

async def setup(bot):
    await bot.add_cog(Auctioneer(bot, bot.db_pool))
