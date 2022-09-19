import discord


class GeoBot(discord.Bot):
    def __init__(self):
        super().__init__()


def main():
    bot = GeoBot()
    bot.run()


if __name__ == "__main__":
    main()
