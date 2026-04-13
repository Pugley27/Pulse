import discord
from discord.ext import commands

# Cog for handling currency-related commands, such as checking balances and updating Cruor. This is where you would implement commands for managing the in-game currency.
class Currency(commands.Cog):

    # The constructor for the Cog, which takes the bot instance as an argument. This allows us to access the bot's API client and configuration from within the Cog.
    def __init__(self, bot):
        self.bot = bot

    # Note the use of @commands.command() and 'self'
    @commands.hybrid_command(name="ping", help="Check if the bot is responsive. Usage: !ping")
    async def ping(self, ctx):
        await ctx.send("Pong!")

    # Command for paying a member Cruor.  This is the org currency command that staff can use to add Cruor to a member's balance. 
    # It checks if the user has the required staff roles before allowing them to execute the command.
    @commands.hybrid_command(name="add_cruor", description="Pay a member Cruor", help="Pay a member Cruor. Admin only. Usage: !add_cruor [member] [amount]")
    async def pay_member(self, ctx, member: discord.Member, amount: int):
        # Check if the user has the required staff roles
        if any(role.id in self.bot.config.STAFF_ROLES for role in ctx.author.roles):
            await ctx.defer()
            # Call the API to update the member's Cruor balance. We pass the member's ID, display name, and the amount to add. The API will handle updating the balance in the database.
            result = await self.bot.api.update_cruor(member.id, member.display_name ,amount)
            if result:
                await ctx.send(f"Added {amount} Cruor to {member.display_name} blood for the blood gods!")
            else:
                await ctx.send("Failed to update Cruor balance.")
        else:
            await ctx.send("You don't have the required permissions to use this command.")

    # Command for checking a member's Cruor balance. This command can be used by anyone to check their own balance or the balance of another member. 
    # It calls the API to fetch the balance and then sends a message with the result.
    @commands.hybrid_command(name="get_balance", description="Check a member's Cruor balance", help="Check a member's Cruor balance. Usage: !get_balance [member]")
    async def get_balance(self, ctx, member: discord.Member):
        target = member or ctx.author
        response = await self.bot.api.get_balance(target.id)
            
        data = response
        await ctx.send(f"💰 {target.display_name} has **{data['balance']} Cruor**.")     

    # This handles errors specifically for this Cog
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("You don't have the required permissions to use this command.")           

# This function is required for main.py to load the file
async def setup(bot):
    await bot.add_cog(Currency(bot))