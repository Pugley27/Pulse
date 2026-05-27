import discord
from discord.ui import View, button

class MarketPaginationView(View):
    def __init__(self, embeds):
        super().__init__(timeout=180) # Timeout after 3 minutes of inactivity
        self.embeds = embeds
        self.current_page = 0

    def update_button_states(self):
        # Disable 'Previous' if on the first page
        self.prev_button.disabled = self.current_page == 0
        # Disable 'Next' if on the last page
        self.next_button.disabled = self.current_page == len(self.embeds) - 1

    @button(label="◀ Previous", style=discord.ButtonStyle.blurple, custom_id="prev_btn")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only let the person who called the command click the buttons
        # (Optional, but highly recommended for admin tools)
        
        self.current_page -= 1
        self.update_button_states()
        
        # CRITICAL FOR EPHEMERAL: You must respond to the interaction directly
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @button(label="Next ▶", style=discord.ButtonStyle.blurple, custom_id="next_btn")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_button_states()
        
        # CRITICAL FOR EPHEMERAL: You must respond to the interaction directly
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)