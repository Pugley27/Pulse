import asyncio
import asyncpg
from datetime import datetime, timezone, timedelta

# Paste your database URI connection string here
DB_URL = "postgresql://postgres:XOVeJeNdvOWrAJdIyBKCRtXtMAuJTmKe@kodama.proxy.rlwy.net:43203/railway"

async def setup_mock_data(pool):
    """Wipes and presets the database state with an item and multiple user bids."""
    async with pool.acquire() as conn:
        print("🧹 Cleaning old test data...")
        await conn.execute("TRUNCATE bids, auctions, auction_items, claimed_items RESTART IDENTITY CASCADE;")
        
        # Ensure a test user balance exists in the lockBox for our bidders
        # Mocking user IDs: 1001, 1002, 1003, 1004, 1005
        print("💰 Setting up mock user balances...")
        for user_id in [1001, 1002, 1003, 1004, 1005]:
            await conn.execute("""
                INSERT INTO "lockBox" (member_id, cruor_amount) 
                VALUES ($1, 5000) 
                ON CONFLICT (member_id) DO UPDATE SET cruor_amount = 5000;
            """, user_id)

        print("📦 Creating an auction batch of 3 items...")
        item_id = await conn.fetchval("""
            INSERT INTO auction_items (name, description, quantity, status, auction_id, holder_id)
            VALUES ('Anvil of the Void', 'A legendary tier testing item', 3, 'listed', 1, 1001)
            RETURNING id;
        """)
        print("📦 Creating an auction batch of 1 items...")
        item_id2 = await conn.fetchval("""
            INSERT INTO auction_items (name, description, quantity, status, auction_id, holder_id)
            VALUES ('Bloods Ear', 'A legendary tier testing item', 10, 'listed', 2, 1001)
            RETURNING id;
        """)


        print("⏰ Scheduling the auction...")
        # Expired 5 minutes ago so the processor loop catches it instantly
        end_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        await conn.execute("""
            INSERT INTO auctions (name, item_id, end_time, status, holder_id)
            VALUES ('Anvil Batch Auction', $1, $2, 'active', 1001);
        """, item_id, end_time)

        await conn.execute("""
            INSERT INTO auctions (name, item_id, end_time, status, holder_id)
            VALUES ('Bloods Ear Auction', $1, $2, 'active', 1001);
        """, item_id2, end_time)

        # Simulate 5 users bidding. Note the tie between user 1003 and 1004.
        # User 1003 bids 250 Cruor slightly BEFORE user 1004.
        print("🔨 Simulating concurrent player bids...")
        bids = [
            (1001, 500, datetime.now(timezone.utc) - timedelta(seconds=10)), # Highest
            (1002, 400, datetime.now(timezone.utc) - timedelta(seconds=8)),  # 2nd
            (1003, 250, datetime.now(timezone.utc) - timedelta(seconds=5)),  # 3rd (Tie breaker winner)
            (1004, 250, datetime.now(timezone.utc) - timedelta(seconds=2)),  # Cutoff tie-breaker loser
            (1005, 100, datetime.now(timezone.utc) - timedelta(seconds=1)),  # Out of range
            
        ]

        for user_id, amount, bid_time in bids:
            await conn.execute("""
                INSERT INTO bids (auction_id, user_id, amount, created_at)
                VALUES (1, $1, $2, $3);
            """, user_id, amount, bid_time)
            print(f"   -> User <@{user_id}> bid {amount} Cruor at {bid_time.strftime('%H:%M:%S')}")

        for user_id, amount, bid_time in bids:
            await conn.execute("""
                INSERT INTO bids (auction_id, user_id, amount, created_at)
                VALUES (2, $1, $2, $3);
            """, user_id, amount, bid_time)
            print(f"   -> User <@{user_id}> bid {amount} Cruor at {bid_time.strftime('%H:%M:%S')}")

async def verify_results(pool):
    """Queries the database database state to ensure the tables match predictions."""
    print("\n📊 Verifying Final Database States:")
    async with pool.acquire() as conn:
        # Check claimed items
        claimed = await conn.fetch("SELECT winner_id, winning_bid FROM claimed_items ORDER BY winning_bid DESC;")
        print(f"📋 Entries inside 'claimed_items' table (Expected: 3): {len(claimed)}")
        for row in claimed:
            print(f"   -> Winner: {row['winner_id']} | Paid: {row['winning_bid']} Cruor")

        # Check leftover inventory
        leftover_stock = await conn.fetchval("SELECT COUNT(*) FROM auction_items WHERE id = 1;")
        print(f"📦 Inventory rows left for this item (Expected: 0): {leftover_stock}")

        # Check remaining balances
        for user_id in [1001, 1002, 1003, 1004]:
            bal = await conn.fetchval('SELECT cruor_amount FROM "lockBox" WHERE member_id = $1;', user_id)
            print(f"💰 User {user_id} End Balance (Started with 5000): {bal} Cruor")

async def main():
    pool = await asyncpg.create_pool(DB_URL)
    try:
        await setup_mock_data(pool)
        #await verify_results(pool)
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())