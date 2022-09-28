import asyncio
import discord
import os
import random
import toml
from discord.ext import tasks
with open("config/config.toml", "r") as config:
    GLOBAL_CONFIG = toml.load(config)

maps = [
    "A Diverse World", "A Community World", "AI Generated World", "A Balanced Canada",
    "A Diverse Sometimes Pinpointable AI Generated Tuas", "Plonk It", "The Daily Challenge",
    "An Arbitrary United States", "A Balanced AI Generated India", "An Extra-Rural Mongolia", "A quiz",
    "A Stochastic Populated Southern Cone", "A Balanced Australia", "An Extraordinary World",
    "A Diverse Complete World", "Phuket Island or Chang Mai"
]


class GeoBot(discord.Bot):

    def __init__(self):
        super().__init__()
        print("Bot has been initialised")

    async def on_ready(self):
        print(f"Bot is ready! Version info: {discord.__version__}")
        await asyncio.sleep(5)
        if not self.change_map.is_running():
            self.change_map.start()

    @tasks.loop(hours=1)
    async def change_map(self):
        await self.change_presence(activity=discord.Game(name=random.choice(maps)))


def main():
    bot = GeoBot()
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            bot.load_extension(f"cogs.{filename[:-3]}")

    bot.run(GLOBAL_CONFIG["TOKEN"])


if __name__ == "__main__":
    main()
