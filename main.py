import discord
import os

class GeoBot(discord.Bot):

    def __init__(self):
        super().__init__()
        print("Bot has been initialised")

    async def on_ready(self):
        print(f"Bot is ready! Version info: {discord.version_info}")


def main():
    bot = GeoBot()
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            bot.load_extension(f"cogs.{filename[:-3]}")

    bot.run()


if __name__ == "__main__":
    main()
