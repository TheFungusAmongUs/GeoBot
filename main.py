import discord


class GeoBot(discord.Bot):

    def __init__(self):
        super().__init__()
        print("Bot has been initialised")

    async def on_ready(self):
        print(f"Bot is ready! Version info: {discord.version_info}")


def main():
    bot = GeoBot()
    bot.run()


if __name__ == "__main__":
    main()
