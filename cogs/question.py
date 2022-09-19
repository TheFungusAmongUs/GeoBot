import discord


class QuestionCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.command()
    async def ask(self):
        pass


def setup(bot):
    bot.add_cog(QuestionCog(bot))
