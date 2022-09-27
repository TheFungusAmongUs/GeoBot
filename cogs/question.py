import asyncio
import discord
import json
import main
from typing import Optional, Type, Union
from utils.enums import QuestionStatus

questions: list["Question"]


def find_all_author_questions(author: Union[discord.Member, discord.User]) -> list["Question"]:
    return [question for question in questions if question.author == author]


async def after_button(view: discord.ui.View, message: discord.Message, question: "Question"):

    view.disable_all_items(exclusions=[view.children[4]])
    question.save()
    await message.edit(view=view)


class Question:

    bot: Type[discord.Bot]

    def __init__(self, title: str, body: str, author: Union[discord.Member, discord.User],
                 status: QuestionStatus = QuestionStatus.IN_REVIEW, id: Optional[int] = None, **kwargs):
        self.status: QuestionStatus = status
        self.title = title
        self.body = body
        self.author = author
        self.id = id

    def make_embed(self):
        return discord.Embed(
            title=self.title,
            description=self.body,
        ).add_field(name="Submitted By", value=f"<@!{self.author.id}>").set_thumbnail(url=self.author.avatar.url)

    @classmethod
    async def from_json(cls, json_object: dict):
        # noinspection PyArgumentList
        json_object.update({"author": await cls.bot.fetch_user(json_object["author"]),
                            "status": QuestionStatus[json_object["status"]]})
        return cls(**json_object)

    def to_json(self):
        return dict(self.__dict__.copy(), **{"author": self.author.id,
                                             "status": self.status.__dict__["_name_"]})

    async def post(self):
        # noinspection PyTypeChecker
        channel: discord.ForumChannel = self.bot.get_channel(main.GLOBAL_CONFIG["IAF_CHANNEL_ID"])
        self.status = QuestionStatus.APPROVED
        await channel.create_thread(name=self.title, content=self.body + f"\n\nOP: {self.author.mention}")

    def save(self):
        for question in questions:
            if question.id == self.id:
                question = self
                break
        else:
            questions.append(self)
        with open("data/data.json", "w") as fp:
            json.dump([q.to_json() for q in questions], fp)


class QuestionModal(discord.ui.Modal):

    def __init__(self, question: Optional[Question] = None, view: Optional[discord.ui.View] = None,
                 message: Optional[discord.Message] = None):
        super().__init__(title="Ask a question/Give feedback")
        self.question = question
        self.view = view
        self.message = message

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
            placeholder="You can add more details here! You can add images when the question has been improved.",
            style=discord.InputTextStyle.paragraph
        ))

    async def callback(self, interaction: discord.Interaction):

        if self.question:
            self.question.title = self.children[0].value
            self.question.body = self.children[1].value
            await self.question.post()
            await interaction.response.send_message("Question has been approved")
            await after_button(self.view, self.message, self.question)
        else:
            new_question = Question(title=self.children[0].value, body=self.children[1].value, author=interaction.user)
            # noinspection PyTypeChecker
            approve_channel: discord.TextChannel = Question.bot.get_channel(main.GLOBAL_CONFIG["APPROVAL_CHANNEL_ID"])
            msg = await approve_channel.send(embed=new_question.make_embed(), view=QuestionApprovalView(new_question))
            await interaction.response.send_message(content="*Question Submitted*",
                                                    embed=new_question.make_embed(), ephemeral=True)
            new_question.id = msg.id
            new_question.save()


class DenyModal(discord.ui.Modal):

    def __init__(self, question: Question, view: discord.ui.View, message: discord.Message):
        super().__init__(title="Deny this question")
        self.add_item(discord.ui.InputText(
            label="Reason",
            placeholder="Why is this question being denied? :("
        ))
        self.question = question
        self.view = view
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.question.author.send(embed=discord.Embed(
                title="Question/Feedback was not accepted",
                description=f"**Please read this carefully:** \n\n"
                            f"Your question/feedback was not accepted for this reason: {self.children[0].value}"
            ).set_footer(text="Please do not ask the same question/give the same feedback, "
                              "instead, try to improve your existing question/feedback")
            )
        except discord.Forbidden:
            await interaction.response.send_message("Question Denied\nUser was not notified: DMs are closed")
        else:
            await interaction.response.send_message("Question Denied\nUser was notified")
        await after_button(self.view, self.message, self.question)


class QuestionApprovalView(discord.ui.View):

    def __init__(self, question: Question):
        super().__init__(timeout=None)
        self.question = question

    @discord.ui.button(style=discord.ButtonStyle.green, label="Approve", custom_id="approve", emoji="📨")
    async def approve_button(self, button: discord.Button, interaction: discord.Interaction):
        await self.question.post()
        await interaction.response.send_message("Question has been approved")
        await after_button(self, self.message, self.question)

    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny", custom_id="deny", emoji="✋")
    async def deny_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(DenyModal(self.question, self, self.message))
        self.question.status = QuestionStatus.DENIED

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Improve", custom_id="improve", emoji="📝")
    async def improve_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(QuestionModal(self.question, self, self.message))

    @discord.ui.button(style=discord.ButtonStyle.red, label="Duplicate", custom_id="duplicate", emoji="🗃️")
    async def duplicate_button(self, button: discord.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(style=discord.ButtonStyle.grey, label="List Questions By Author", custom_id="list", emoji="📋")
    async def list_questions(self, button: discord.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Questions from {self.question.author}",
            description="\n".join([f"\\> [{q.title}](https://discord.com/channels/{main.GLOBAL_CONFIG['GUILD_ID']}/"
                                   f"{main.GLOBAL_CONFIG['APPROVAL_CHANNEL_ID']}/{self.question.id}): {q.status.name}"
                                   for q in find_all_author_questions(self.question.author)])
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CreatePostView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Post", emoji="📝", style=discord.ButtonStyle.green, custom_id="create")
    async def create_post_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(QuestionModal())


class QuestionCog(discord.Cog):

    def __init__(self, bot):
        Question.bot = bot
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        global questions
        await asyncio.sleep(2)
        # noinspection PyTypeChecker
        approve_channel: discord.TextChannel = self.bot.get_channel(main.GLOBAL_CONFIG["APPROVAL_CHANNEL_ID"])
        with open("data/data.json", "r") as fp:
            questions = [await Question.from_json(q) for q in json.load(fp)]
        for question in questions:
            view = QuestionApprovalView(question)
            view.message = await approve_channel.fetch_message(question.id)
            self.bot.add_view(view=view, message_id=question.id)
        print("Views have been loaded")
        # noinspection PyTypeChecker
        create_post_channel: discord.TextChannel = self.bot.get_channel(
            main.GLOBAL_CONFIG["CREATE_POST_CHANNEL_ID"]
        )
        if not await create_post_channel.history().flatten():
            embed = discord.Embed(
                title="Create Post",
                description="You can create a post by clicking on the button below :)\n\n"
                            "Feel free to give your feedback or ask any questions,"
                            " just make sure it's on topic and constructive!"
            )
            await create_post_channel.send(embed=embed, view=CreatePostView())
        else:
            self.bot.add_view(CreatePostView())


def setup(bot):
    bot.add_cog(QuestionCog(bot))
