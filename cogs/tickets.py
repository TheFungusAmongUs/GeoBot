import discord


class TicketModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Create a ticket")

        self.add_item(discord.ui.InputText(
            label="Ticket title",
            placeholder="Enter a concise, specific title detailing the problem",
            min_length=10,
            max_length=100
        ))
        self.add_item(discord.ui.InputText(
            label="Ticket Body",
            placeholder="You can elaborate on the problem here",
            min_length=10
        ))


class TicketCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(TicketCog(bot))
