from email.utils import format_datetime
from dateutil import parser
import discord
from discord.ext import commands
from cogs.paginator import MarketPaginationView


# Cog for handling auction-related commands. This is where you would implement commands for creating auctions, bidding, etc.
class Auctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Returns a list of all the items that have been added for auction with their IDs, names, and descriptions. This command can be used by anyone to see what items are available for auction.
    @commands.hybrid_command(name="list_items", description="List all items available for auction", help="List all items available for auction. Usage: !list_items")
    async def list_items(self, ctx):
        # 1. Defer immediately so the interaction doesn't timeout during the API/Fetch loops
        await ctx.defer()

        response = await self.bot.api.get_items()
        
        if not response or "items" not in response:
            await ctx.send("Failed to retrieve items.")
            return

        items = response["items"]
        if not items:
            await ctx.send("There are currently no items available for auction.")
            return

        # 2. Process and build the individual string entries for each item
        formatted_items = []
        for item in items:    
            winner = await self.bot.fetch_user(item['member_id']) if item['member_id'] else 'None'
            holder = await self.bot.fetch_user(item['holder_id']) if item['holder_id'] else 'None'
            
            item_string = (
                f"**ID:** {item['id']} - **{item['name']}**\n"
                f"📝 *{item['description']}*\n"
                f"Status: `{item['status']}` | Auction ID: `{item['auction_id']}`\n"
                f"Winner: {winner} | Holder: {holder}"
            )
            formatted_items.append(item_string)

        # 3. Chunk the items (e.g., 4 items per page so the embed stays clean and readable)
        items_per_page = 6
        chunks = [formatted_items[i:i + items_per_page] for i in range(0, len(formatted_items), items_per_page)]
        
        # 4. Generate the Embed pages
        embeds = []
        for index, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="🔨 Current Auction Items", 
                color=discord.Color.blue()
            )
            # Separate each item in the chunk with a clean horizontal line
            embed.description = "\n\n---\n\n".join(chunk)
            embed.set_footer(text=f"Page {index + 1} of {len(chunks)}")
            embeds.append(embed)

        # 5. Send the response
        if len(embeds) == 1:
            # No buttons needed if everything fits on one page
            await ctx.send(embed=embeds[0])
        else:
            # Initialize view, set button logic, and send
            view = MarketPaginationView(embeds)
            view.update_button_states() 
            await ctx.send(embed=embeds[0], view=view)
    
    # Command calls the api to find all the active auctions and sends a message with the results. Results include the auction ID, name, item name, and end time formatted with date and time in DD/MM/YYYY HH:MM format. This command can be used by anyone to see what auctions are currently active.
    @commands.hybrid_command(name="list_auctions", description="List all active auctions", help="List all active auctions. Usage: !list_auctions")
    async def list_auctions(self, ctx):
        # Call the API to get the list of active auctions. The API will return a list of auctions with their details.
        response = await self.bot.api.get_active_auctions()
        if response and "auctions" in response:
            auctions = response["auctions"]
            if auctions:
                auction_list = "\n".join([f"ID: {auction['id']} - {auction['name']} (Item: {auction['item_name']}) - Ends: <t:{int(parser.parse(auction['end_time']).timestamp())}:f>" for auction in auctions])
                await ctx.send(f"**Active Auctions:**\n{auction_list}")
            else:
                await ctx.send("There are currently no active auctions.")
        else:
            await ctx.send("Failed to retrieve auctions.")

# Command calls the api to find all the active auctions and sends a message with the results. 
    # Results include the auction ID, name, item name, and end time formatted cleanly.
    @commands.hybrid_command(name="list_auctions", description="List all active auctions", help="List all active auctions. Usage: !list_auctions")
    async def list_auctions(self, ctx):
        # 1. Defer immediately to prevent interaction timeouts during processing
        await ctx.defer()

        # Call the API to get the list of active auctions.
        response = await self.bot.api.get_active_auctions()
        
        if not response or "auctions" not in response:
            await ctx.send("Failed to retrieve auctions.")
            return

        auctions = response["auctions"]
        if not auctions:
            await ctx.send("There are currently no active auctions.")
            return

        # 2. Process and format individual auction entries
        formatted_auctions = []
        for auction in auctions:
            try:
                # Convert the ISO/string timestamp to a Unix int for Discord's dynamic timestamp rendering
                end_timestamp = int(parser.parse(auction['end_time']).timestamp())
                time_relative = f"<t:{end_timestamp}:R>"  # e.g., "in 2 hours"
                time_absolute = f"<t:{end_timestamp}:f>"  # e.g., "May 17, 2026 4:00 PM"
                end_time_str = f"{time_absolute} ({time_relative})"
            except Exception:
                # Fallback string if parser encounters an unexpected date format
                end_time_str = f"`{auction['end_time']}`"

            auction_string = (
                f"🆔 **Auction ID:** `{auction['id']}`\n"
                f"🏆 **Event:** {auction['name']}\n"
                f"📦 **Item:** *{auction['item_name']}*\n"
                f"⏳ **Ends:** {end_time_str}"
            )
            formatted_auctions.append(auction_string)

        # 3. Chunk the auctions (5 per page fits beautifully in an embed)
        auctions_per_page = 6
        chunks = [formatted_auctions[i:i + auctions_per_page] for i in range(0, len(formatted_auctions), auctions_per_page)]

        # 4. Generate the Embed pages
        embeds = []
        for index, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="🚨 Active Market Auctions", 
                color=discord.Color.gold()  # Distinct color for auctions vs standard items
            )
            embed.description = "\n\n---\n\n".join(chunk)
            embed.set_footer(text=f"Page {index + 1} of {len(chunks)}")
            embeds.append(embed)

        # 5. Deliver the paginated response
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            view = MarketPaginationView(embeds)
            view.update_button_states()
            await ctx.send(embed=embeds[0], view=view)

    # Add an item for auction. This is a simple command that takes a name and description for the item. Other commands for starting auctions, placing bids, etc. would be implemented similarly.
    @commands.hybrid_command(name="add_item", description="Add an item to the auction", help="Add an item to the auction. Admin only. Usage: !add_item [name] [description]", property="admin")
    async def add_item(self, ctx, name: str, description: str):
         if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.add_item(name, description, ctx.author.id)
            await ctx.send(f"{name} added to the auction items with ID: {response['item_id']}")

    # Add an item for auction. This is a simple command that takes a name and description for the item. Other commands for starting auctions, placing bids, etc. would be implemented similarly.
    @commands.hybrid_command(name="add_auction", description="Create a new auction with an item", help="Create a new auction with an item. Admin only. Usage: !add_auction [name] [description] [item_id]")
    async def add_auction(self, ctx, name: str, description: str, item_id: int):
         if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.add_auction(name, description, item_id)
            print(f"API response for add_auction: {response}")  # Debugging statement to check the API response
            # Check the response to make sure the auction was created successfully and send a message with the details. The API should return the auction ID, name, item name.
            if response and "auction_id" in response:   
                await ctx.send(f"{name} auction created with ID: {response['auction_id']} for item: {response['item_name']}")
            else:
                # If the response doesn't contain the expected data, send an error message. This could happen if the item ID is invalid or if there was an issue with the API request with details about the error if available.
                await ctx.send("Failed to create the auction. Please check the item ID and try again. Error details: " + (response.get("detail", "No additional error information provided.")))
    
    # Command to allow a user to bid for an active auction. This command would take the auction ID and the bid amount as arguments. It would call the API to place the bid and then send a message with the result, including whether the bid was successful or if it was too low, etc.
    @commands.hybrid_command(name="bid", description="Place a bid on an active auction", help="Place a bid on an active auction. Usage: !bid [auction_id] [amount]")
    async def place_bid(self, ctx, auction_id: int, amount: int):     
        response = await self.bot.api.place_bid( ctx.author.id, auction_id, amount)
        if response and "status" in response:
            if response["status"] == "success":
                await ctx.send(f"Your bid has been placed successfully!")
            else:
                await ctx.send(f"Failed to place bid: {response.get('detail', 'No additional error information provided.')}")
        else:
            await ctx.send("Failed to place bid. " + (response.get("detail", "No additional error information provided.")))

    # this command will close out an auction when the item has been sold. This would be used by the auctioneer to finalize the auction and determine the winner. The API would return the details of the winning bid, including the user ID of the winner, the winning bid amount, and the item that was sold.
    @commands.hybrid_command(name="close_auction", description="Close an active auction", help="Close an active auction. Admin only. Usage: !close_auction [auction_id]")
    async def close_auction(self, ctx, auction_id: int):
        if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.close_auction(auction_id)
            if response and "status" in response:
                if response["status"] == "success":
                    auction_id = response.get("auction_id")
                    winner_id = response.get("winner_id")
                    item_name = response.get("item_name")
                    holder_id = response.get("holder_id")
                    winner_user = await self.bot.fetch_user(winner_id) if winner_id else "Unknown User"
                    holder_user = await self.bot.fetch_user(holder_id) if holder_id else "Unknown User"
                    await ctx.send(f"Auction {auction_id} closed successfully! Winner: {winner_user} has been awarded the item: {item_name} from {holder_user}.")
                else:
                    await ctx.send(f"Failed to close auction: {response.get('detail', 'No additional error information provided.')}")
            else:
                await ctx.send("Failed to close auction. " + (response.get("detail", "No additional error information provided.")))
        else:
            await ctx.send("You don't have the required permissions to use this command.")

    # This is an admin command to list all the active bids for a specific auction. This would be useful for the auctioneer to see who has placed bids and what the current highest bid is. The API would return a list of bids with the user ID, bid amount, and timestamp.
    @commands.hybrid_command(name="list_bids", description="List all bids for a specific auction", help="List all bids for a specific auction. Admin only. Usage: !list_bids [auction_id]")
    async def list_bids(self, ctx, auction_id: int):
        if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.get_bids(auction_id)
            if response and "bids" in response:
                bids = response["bids"]
                bid_list = ""
                if bids:
                    # For each bid, we can also try to fetch the user information from Discord to display their username instead of just their user ID. This is optional but can make the output more user-friendly.
                    for bid in bids:    
                        try:
                            user = await self.bot.fetch_user(bid['user_id'])
                        except discord.NotFound:
                            print("No user exists with that ID.")        
                                    
                        bid_list += f"User ID: {user} - Amount: {bid['amount']} Cruor\n"

                    await ctx.send(f"**Bids for Auction ID {auction_id}:**\n{bid_list}")
                else:
                    await ctx.send(f"There are currently no bids for auction ID {auction_id}.")
            else:
                await ctx.send("Failed to retrieve bids. Please check the auction ID and try again.")
        else:
            await ctx.send("You don't have the required permissions to use this command.")
            
    def safe_format(self,date_str):
        try:
            return parser.parse(date_str).strftime('%m/%d/%Y %H:%M:%S')
        except (ValueError, TypeError):
            return "Unknown Date" 

    # Command for an admin to list auctions that have been created but not yet started. 
    # This is useful for managing auctions and seeing what items are scheduled to be auctioned.
    @commands.hybrid_command(name="list_upcoming", description="List all auctions that have not yet started", help="List all auctions that have not yet started. Admin only. Usage: !list_upcoming")
    async def list_upcoming_auctions(self, ctx):
        # Check permissions using your config staff roles
        if not any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            await ctx.send("You don't have the required permissions to use this command.", ephemeral=True)
            return

        # 1. Defer immediately after permissions pass to avoid gateway timeouts
        await ctx.defer()

        response = await self.bot.api.get_unscheduled_auctions()
        
        if not response or "auctions" not in response:
            await ctx.send("Failed to retrieve unscheduled auctions.")
            return

        auctions = response["auctions"]
        if not auctions:
            await ctx.send("There are currently no unscheduled auctions.")
            return

        # 2. Process and format individual upcoming auction entries
        formatted_upcoming = []
        for auction in auctions:
            auction_string = (
                f"🆔 **Auction ID:** `{auction['id']}`\n"
                f"📋 **Draft Name:** {auction['name']}\n"
                f"📦 **Item:** **{auction['item_name']}**\n"
                f"📝 **Description:** *{auction['description']}*"
            )
            formatted_upcoming.append(auction_string)

        # 3. Chunk the items (5 per page keeps the admin interface neat)
        items_per_page = 5
        chunks = [formatted_upcoming[i:i + items_per_page] for i in range(0, len(formatted_upcoming), items_per_page)]

        # 4. Generate the Embed pages
        embeds = []
        for index, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="⚙️ Unscheduled / Upcoming Auctions", 
                color=discord.Color.purple()  # Distinct admin color
            )
            embed.description = "\n\n---\n\n".join(chunk)
            embed.set_footer(text=f"Admin View | Page {index + 1} of {len(chunks)}")
            embeds.append(embed)

        # 5. Deliver the paginated response
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            view = MarketPaginationView(embeds)
            view.update_button_states()
            await ctx.send(embed=embeds[0], view=view)

    # Command that finds the listed auction and makes it active, setting a start time and end time based on the specified duration. This would be used to start an auction that has been created with the add_auction command.
    @commands.hybrid_command(name="start_auction", description="Start an auction by ID", help="Start an auction by ID. Admin only. Usage: !start_auction [auction_id] [duration_minutes]")
    async def start_auction(self, ctx, auction_id: int, duration_minutes: int):
        if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.start_auction(auction_id, duration_minutes)
            if response and "auction_id" in response:
                await ctx.send(f"Auction ID: {response['auction_id']} has been started and will end at <t:{int(parser.parse(response['end_time']).timestamp())}:f>.")
            else:
                await ctx.send("Failed to start the auction. Please check the auction ID and try again.")


    # This handles errors specifically for this Cog
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("You don't have the required permissions to use this command.")           

# This function is required for main.py to load the file
async def setup(bot):
    await bot.add_cog(Auctions(bot))





