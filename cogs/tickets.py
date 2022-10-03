import discord


class TicketCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(TicketCog(bot))
