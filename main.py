import discord


class GeoBot(discord.Bot):
    def __init__(self):
        super().__init__()
        self.add_commands()

    def add_commands(self):
        pass


def main():
    bot = GeoBot()
    bot.run()


if __name__ == "__main__":
    main()
