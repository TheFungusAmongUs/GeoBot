import discord
import os
import toml


class GeoBot(discord.Bot):

    def __init__(self):
        super().__init__()
        print("Bot has been initialised")
        with open("config/config.toml", "r") as config:
            self.GLOBAL_CONFIG = toml.load(config)

    async def on_ready(self):
        print(f"Bot is ready! Version info: {discord.__version__}")


def main():
    bot = GeoBot()
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            bot.load_extension(f"cogs.{filename[:-3]}")

    bot.run(bot.GLOBAL_CONFIG["TOKEN"])


if __name__ == "__main__":
    main()
