import discord
from typing import Optional, Type, Union


class Question:

    def __init__(self, title: str, body: str, author: Union[discord.Member, discord.User],
                 closed: Optional[bool] = False):
        self.title = title
        self.body = body
        self.author = author
        self.closed = closed

    def make_embed(self):
        return discord.Embed(
            title=self.title,
            description=self.body,
        ).add_field(name="Submitted By", value=f"<@!{self.author.id}>").set_thumbnail(url=self.author.avatar.url)

    @classmethod
    def from_json(cls, json_object: dict, bot: Type[discord.Bot]):
        # noinspection PyArgumentList
        return cls(**json_object.update({"author": bot.get_user(json_object["author"])}))

    def to_json(self):
        return self.__dict__.update({"author": self.author.id})


class QuestionCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.command()
    async def ask(self):
        pass


def setup(bot):
    bot.add_cog(QuestionCog(bot))
