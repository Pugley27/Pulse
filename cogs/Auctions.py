from email.utils import format_datetime
from dateutil import parser
import discord
from discord.ext import commands

# Cog for handling auction-related commands. This is where you would implement commands for creating auctions, bidding, etc.
class Auctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Returns a list of all the items that have been added for auction with their IDs, names, and descriptions. This command can be used by anyone to see what items are available for auction.
    @commands.hybrid_command(name="list_items", description="List all items available for auction", help="List all items available for auction. Usage: !list_items")
    async def list_items(self, ctx):
        response = await self.bot.api.get_items()
        if response and "items" in response:
            items = response["items"]
            if items:
                item_list = "\n".join([f"ID: {item['id']} - {item['name']}: {item['description']}" for item in items])
                await ctx.send(f"**Items Available for Auction:**\n{item_list}")
            else:
                await ctx.send("There are currently no items available for auction.")
        else:
            await ctx.send("Failed to retrieve items.")

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

    # Add an item for auction. This is a simple command that takes a name and description for the item. Other commands for starting auctions, placing bids, etc. would be implemented similarly.
    @commands.hybrid_command(name="add_item", description="Add an item to the auction", help="Add an item to the auction. Admin only. Usage: !add_item [name] [description]", property="admin")
    async def add_item(self, ctx, name: str, description: str):
         if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.add_item(name, description)
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
                await ctx.send(f"Your bid of {amount} Cruor for auction ID {auction_id} has been placed successfully!")
            else:
                await ctx.send(f"Failed to place bid: {response.get('detail', 'No additional error information provided.')}")
        else:
            await ctx.send("Failed to place bid. Please check the auction ID and try again.")

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

    # Command for an admin to list auctions that have been created but not yet started. This is useful for managing auctions and seeing what items are scheduled to be auctioned. The API will return a list of auctions with their details, including the item name and description.
    @commands.hybrid_command(name="list_upcoming", description="List all auctions that have not yet started", help="List all auctions that have not yet started. Admin only. Usage: !list_upcoming")
    async def list_upcoming_auctions(self, ctx):
        if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.get_unscheduled_auctions()
            if response and "auctions" in response:
                auctions = response["auctions"]
                if auctions:
                    auction_list = "\n".join([f"ID: {auction['id']} - {auction['name']} (Item: {auction['item_name']}) - Description: {auction['description']}" for auction in auctions])
                    await ctx.send(f"**UnScheduled Auctions:**\n{auction_list}")
                else:
                    await ctx.send("There are currently no unscheduled auctions.")
            else:
                await ctx.send("Failed to retrieve unscheduled auctions.")
        else:
            await ctx.send("You don't have the required permissions to use this command.")

    # Command that finds the listed auction and makes it active, setting a start time and end time based on the specified duration. This would be used to start an auction that has been created with the add_auction command.
    @commands.hybrid_command(name="start_auction", description="Start an auction by ID", help="Start an auction by ID. Admin only. Usage: !start_auction [auction_id] [duration_minutes]")
    async def start_auction(self, ctx, auction_id: int, duration_minutes: int):
        if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.start_auction(auction_id, duration_minutes)
            if response and "auction_id" in response:
                await ctx.send(f"Auction ID: {response['auction_id']} has been started and will end at {response['end_time']}.")
            else:
                await ctx.send("Failed to start the auction. Please check the auction ID and try again.")


    # This handles errors specifically for this Cog
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("You don't have the required permissions to use this command.")           

# This function is required for main.py to load the file
async def setup(bot):
    await bot.add_cog(Auctions(bot))





