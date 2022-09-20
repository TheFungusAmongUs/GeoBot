import discord
import main
from typing import Optional, Type, Union


class Question:

    bot: Type[discord.Bot]

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

    async def create(self):
        # noinspection PyTypeChecker
        channel: discord.ForumChannel = self.bot.get_channel(main.GLOBAL_CONFIG["IAF_CHANNEL_ID"])
        await channel.create_thread(name=self.title, content=self.body + f"\n\nOP: {self.author.mention}")


class QuestionModal(discord.ui.Modal):

    def __init__(self, question: Optional[Question] = None):
        super().__init__(title="Ask a question/Give feedback")
        self.question = question

        self.add_item(discord.ui.InputText(
            label="Question/Feedback Title",
            min_length=10,
            max_length=100,
            value=getattr(question, "title", __default=None)
        ))

        self.add_item(discord.ui.InputText(
            label="Question/Feedback Body",
            min_length=10,
            max_length=2000,
            value=getattr(question, "body", __default=None)
        ))

    async def callback(self, interaction: discord.Interaction):
        new_question = Question(title=self.children[0].value, body=self.children[1].value, author=interaction.user)
        if self.question:
            await self.question.create()
            return

        # noinspection PyTypeChecker
        approve_channel: discord.TextChannel = Question.bot.get_channel(main.config["APPROVE_CHANNEL_ID"])
        await approve_channel.send(embed=new_question.make_embed(), view=QuestionApprovalView(new_question))


class QuestionApprovalView(discord.ui.View):

    def __init__(self, question: Question):
        super().__init__(timeout=None)
        self.question = question

    @discord.ui.button(style=discord.ButtonStyle.green, label="Approve")
    async def approve_button(self, button: discord.Button, interaction: discord.Interaction):
        await self.question.create()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny")
    async def deny_button(self, button: discord.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Improve")
    async def improve_button(self, button: discord.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(style=discord.ButtonStyle.red, label="Duplicate")
    async def duplicate_button(self, button: discord.Button, interaction: discord.Interaction):
        pass


class QuestionCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot
        Question.bot = bot

    @discord.command(guild_ids=[main.GLOBAL_CONFIG["GUILD_ID"]])
    async def ask(
            self, ctx: discord.ApplicationContext,
            question_title: discord.Option(
                required=True,
                input_type=str,
                description="Please include a brief, specific question title",
                max_length=100
            ),
            question_body: discord.Option(
                required=True,
                input_type=str,
                description="You can add more details in the question body"
            )
    ):
        # noinspection PyTypeChecker
        question = Question(question_title, question_body, ctx.author)




def setup(bot):
    bot.add_cog(QuestionCog(bot))
