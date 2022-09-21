import discord
import main
from typing import Optional, Type, Union
from utils.enums import QuestionStatus


class Question:

    bot: Type[discord.Bot]

    def __init__(self, title: str, body: str, author: Union[discord.Member, discord.User],
                 status: QuestionStatus = QuestionStatus.IN_REVIEW):
        self.status: QuestionStatus = status
        self.title = title
        self.body = body
        self.author = author

    def make_embed(self):
        return discord.Embed(
            title=self.title,
            description=self.body,
        ).add_field(name="Submitted By", value=f"<@!{self.author.id}>").set_thumbnail(url=self.author.avatar.url)

    @classmethod
    def from_json(cls, json_object: dict):
        # noinspection PyArgumentList
        return cls(**json_object.update({"author": cls.bot.get_user(json_object["author"])}))

    def to_json(self):
        return self.__dict__.copy().update({"author": self.author.id})

    async def create(self):
        # noinspection PyTypeChecker
        channel: discord.ForumChannel = self.bot.get_channel(main.GLOBAL_CONFIG["IAF_CHANNEL_ID"])
        self.status = QuestionStatus.APPROVED
        await channel.create_thread(name=self.title, content=self.body + f"\n\nOP: {self.author.mention}")


class QuestionModal(discord.ui.Modal):

    def __init__(self, question: Optional[Question] = None):
        super().__init__(title="Ask a question/Give feedback")
        self.question = question

        self.add_item(discord.ui.InputText(
            label="Question/Feedback Title",
            min_length=10,
            max_length=100,
            value=getattr(question, "title", None),
            placeholder="Enter a concise, specific title"
        ))

        self.add_item(discord.ui.InputText(
            label="Question/Feedback Body",
            min_length=10,
            max_length=2000,
            value=getattr(question, "body", None),
            placeholder="You can add more details here! You can add images when the question has been improved."
        ))

    async def callback(self, interaction: discord.Interaction):
        new_question = Question(title=self.children[0].value, body=self.children[1].value, author=interaction.user)
        if self.question:
            await new_question.create()
            new_question.status = QuestionStatus.APPROVED
            return

        # noinspection PyTypeChecker
        approve_channel: discord.TextChannel = Question.bot.get_channel(main.GLOBAL_CONFIG["APPROVAL_CHANNEL_ID"])
        await approve_channel.send(embed=new_question.make_embed(), view=QuestionApprovalView(new_question))
        await interaction.response.send_message(content="*Question Submitted*",
                                                embed=new_question.make_embed(), ephemeral=True)


class DenyModal(discord.ui.Modal):

    def __init__(self, question: Question):
        super().__init__(title="Deny this question")
        self.add_item(discord.ui.InputText(
            label="Reason",
            placeholder="Why is this question being denied? :("
        ))
        self.question = question

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.question.author.send(embed=discord.Embed(
                title="Question/Feedback was not accepted",
                description=f"**Please read this carefully:** \n\n"
                            f"Your question/feedback was not accepted for this reason: {self.children[0].value}"
            ).set_footer(text="Please do not ask the same question/give the same feedback, "
                              "instead, try to improve your existing question")
            )
        except discord.Forbidden:
            await interaction.response.send_message("User was not notified: DMs are closed", ephemeral=True)
        else:
            await interaction.response.send_message("User was notified", ephemeral=True)


class QuestionApprovalView(discord.ui.View):

    def __init__(self, question: Question):
        super().__init__(timeout=None)
        self.question = question

    async def _scheduled_task(self, item: discord.ui.Item, interaction: discord.Interaction):
        await super()._scheduled_task(item, interaction)
        self.disable_all_items()
        await self.message.edit(view=self)

    @discord.ui.button(style=discord.ButtonStyle.green, label="Approve")
    async def approve_button(self, button: discord.Button, interaction: discord.Interaction):
        await self.question.create()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny")
    async def deny_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(DenyModal(self.question))
        self.question.status = QuestionStatus.DENIED

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Improve")
    async def improve_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(QuestionModal(self.question))

    @discord.ui.button(style=discord.ButtonStyle.red, label="Duplicate")
    async def duplicate_button(self, button: discord.Button, interaction: discord.Interaction):
        pass


class QuestionCog(discord.Cog):

    def __init__(self, bot):
        Question.bot = bot

    @discord.command(guild_ids=[main.GLOBAL_CONFIG["GUILD_ID"]])
    async def ask(self, ctx: discord.ApplicationContext):
        await ctx.response.send_modal(QuestionModal())


def setup(bot):
    bot.add_cog(QuestionCog(bot))
