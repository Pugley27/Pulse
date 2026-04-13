from email.utils import format_datetime
from dateutil import parser
from discord.ext import commands

# Cog for handling auction-related commands. This is where you would implement commands for creating auctions, bidding, etc.
class Auctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Add an item for auction. This is a simple command that takes a name and description for the item. Other commands for starting auctions, placing bids, etc. would be implemented similarly.
    @commands.hybrid_command(name="add_item", description="Add an item to the auction", help="Add an item to the auction. Admin only. Usage: !add_item [name] [description]")
    async def add_item(self, ctx, name: str, description: str):
         if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            response = await self.bot.api.add_item(name, description)
            await ctx.send(f"{name} added to the auction items with ID: {response['item_id']}")

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
    
    def safe_format(self,date_str):
        try:
            return parser.parse(date_str).strftime('%m/%d/%Y %H:%M:%S')
        except (ValueError, TypeError):
            return "Unknown Date"
    
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





