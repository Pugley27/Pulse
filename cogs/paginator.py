import discord
from discord.ext import commands

# 1. Define the Button View for Pagination
class MarketPaginationView(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0

    async def update_message(self, interaction: discord.Interaction):
        """Helper function to edit the message with the new page and update button states."""
        self.update_button_states()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    def update_button_states(self):
        """Disables buttons if you hit the boundaries."""
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.blurple, disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)

    async def on_timeout(self):
        """Fires when the buttons expire; disables everything so it's not a dead UI."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        # Note: To update the message on timeout, you'll need to store the message object, 
        # but disabling future clicks out-of-the-box prevents errors.


