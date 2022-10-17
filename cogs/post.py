import asyncio
import discord
import json
import main
from typing import Optional, Union
from utils.enums import PostStatus, PostType

posts: list["Post"]


def find_all_author_posts(author: Union[discord.Member, discord.User]) -> list["Post"]:
    return [post for post in posts if post.author == author]


class Post:

    bot: discord.Bot

    def __init__(self, title: str, values: dict[str, str], author: Union[discord.Member, discord.User], type: PostType,
                 status: PostStatus = PostStatus.IN_REVIEW, id: Optional[int] = None):
        self.status: PostStatus = status
        self.title = title
        self.values = values
        self.author = author
        self.id = id
        self.type = type

    def make_embed(self):
        embed = discord.Embed(
            title=self.title
        ).add_field(name="Submitted By", value=f"<@!{self.author.id}>").set_thumbnail(url=self.author.avatar.url)
        for title, content in self.values.items():
            embed.add_field(name=title, value=content)
        return embed

    @classmethod
    async def from_json(cls, json_object: dict):
        # noinspection PyArgumentList
        json_object.update({"author": await cls.bot.fetch_user(json_object["author"]),
                            "status": PostStatus[json_object["status"]],
                            "type": PostType[json_object["type"]]})
        return cls(**json_object)

    def to_json(self):
        return dict(self.__dict__.copy(), **{"author": self.author.id,
                                             "status": self.status.name,
                                             "type": self.type.name})

    async def post(self):
        # noinspection PyTypeChecker
        channel: discord.ForumChannel = self.bot.get_channel(main.GLOBAL_CONFIG[self.type.value])
        self.status = PostStatus.APPROVED
        await channel.create_thread(name=self.title, embed=self.make_embed())

    def save(self):
        for post in posts:
            if post.id == self.id:
                post = self
                break
        else:
            posts.append(self)
        with open("data/posts.json", "w") as fp:
            json.dump([q.to_json() for q in posts], fp)


class PostModal(discord.ui.Modal):

    def __init__(self, _type: PostType, post: Optional[Post] = None, view: Optional["PostApprovalView"] = None):

        self.post = post
        self.view = view
        self.type = _type
        if _type == PostType.FEEDBACK_QUESTION:
            title = "Ask a question/Give feedback"
            items = [
                discord.ui.InputText(
                    label="Post/Feedback Title",
                    min_length=10,
                    max_length=100,
                    value=getattr(post, "title", None),
                    placeholder="Enter a concise, specific title"
                ),
                discord.ui.InputText(
                    label="Post/Feedback Body",
                    min_length=10,
                    max_length=2000,
                    value=getattr(post, "values", {"Post/Feedback Body": ""})["Post/Feedback Body"],
                    placeholder="You can add more details here! You can add images when the post has been improved.",
                    style=discord.InputTextStyle.paragraph
                )
            ]
        elif _type == PostType.BUG_REPORT:
            title = "Create a bug report"
            items = [
                discord.ui.InputText(
                    label="Issue Title",
                    placeholder="Enter a brief description of the error.",
                    value=getattr(post, "title", None),
                    max_length=100
                ),
                discord.ui.InputText(
                    label="Steps to reproduce the issue",
                    placeholder="What do you need for the issue to arise?",
                    value=getattr(post, "values", {"Steps to reproduce the issue": ""})["Steps to reproduce the issue"],
                    style=discord.InputTextStyle.paragraph
                ),
                discord.ui.InputText(
                    label="What is the expected result?",
                    placeholder="Please enter the expected result, even if it's obvious :)",
                    value=getattr(post, "values", {"What is the expected result?": ""})["What is the expected result?"],
                    style=discord.InputTextStyle.paragraph
                ),
                discord.ui.InputText(
                    label="What's the actual result?",
                    placeholder="Please enter the actual result here",
                    value=getattr(post, "values", {"What's the actual result?": ""})["What's the actual result?"],
                    style=discord.InputTextStyle.paragraph
                ),
                discord.ui.InputText(
                    label="Additional Details",
                    placeholder="Is there anything more you want to add?",
                    value=getattr(post, "values", {"Additional Details": ""})["Additional Details"],
                    style=discord.InputTextStyle.paragraph
                )
            ]
        super().__init__(title=title)
        for item in items:
            self.add_item(item)

    async def callback(self, interaction: discord.Interaction):

        if self.post:
            self.post.title = self.children[0].value
            self.post.values = {child.label: child.value for child in self.children[1:]}
            await self.post.post()
            await interaction.response.send_message("Post has been approved")
            await self.view.after_button()
        else:
            new_post = Post(title=self.children[0].value, author=interaction.user, type=self.type,
                            values={child.label: child.value for child in self.children[1:]})
            # noinspection PyTypeChecker
            approve_channel: discord.TextChannel = Post.bot.get_channel(main.GLOBAL_CONFIG["APPROVAL_CHANNEL_ID"])
            msg = await approve_channel.send(embed=new_post.make_embed(), view=PostApprovalView(new_post))
            await interaction.response.send_message(content="*Post Submitted*",
                                                    embed=new_post.make_embed(), ephemeral=True)
            new_post.id = msg.id
            new_post.save()


class DenyModal(discord.ui.Modal):

    def __init__(self, post: Post, view: "PostApprovalView"):
        super().__init__(title="Deny this post")
        self.add_item(discord.ui.InputText(
            label="Reason",
            placeholder="Why is this post being denied? :("
        ))
        self.post = post
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.post.author.send(embed=discord.Embed(
                title="Post/Feedback was not accepted",
                description=f"**Please read this carefully:** \n\n"
                            f"Your post/feedback was not accepted for this reason: {self.children[0].value}"
            ).set_footer(text="Please do not ask the same post/give the same feedback, "
                              "instead, try to improve your existing post/feedback")
            )
        except discord.Forbidden:
            await interaction.response.send_message("Post Denied\nUser was not notified: DMs are closed")
        else:
            await interaction.response.send_message("Post Denied\nUser was notified")
        await self.view.after_button()


class PostApprovalView(discord.ui.View):

    def __init__(self, post: Post):
        super().__init__(timeout=None)
        self.post = post

    @discord.ui.button(style=discord.ButtonStyle.green, label="Approve", custom_id="approve", emoji="📨")
    async def approve_button(self, button: discord.Button, interaction: discord.Interaction):
        await self.post.post()
        await interaction.response.send_message("Post has been approved")
        await self.after_button()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny", custom_id="deny", emoji="✋")
    async def deny_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(DenyModal(self.post, self))
        self.post.status = PostStatus.DENIED

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Improve", custom_id="improve", emoji="📝")
    async def improve_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PostModal(self.post.type, self.post, self))

    @discord.ui.button(style=discord.ButtonStyle.red, label="Duplicate", custom_id="duplicate", emoji="🗃️")
    async def duplicate_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_message(content="Hmmm, you haven't unlocked that yet", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.grey, label="List Posts By Author", custom_id="list", emoji="📋")
    async def list_posts(self, button: discord.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Posts from {self.post.author}",
            description="\n".join([f"\\> [{q.title}](https://discord.com/channels/{main.GLOBAL_CONFIG['GUILD_ID']}/"
                                   f"{main.GLOBAL_CONFIG['APPROVAL_CHANNEL_ID']}/{self.post.id}): {q.status.name}"
                                   for q in find_all_author_posts(self.post.author)])
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def after_button(self):
        self.disable_all_items(exclusions=[self.children[4]])
        self.post.save()
        await self.message.edit(view=self)


class PostCog(discord.Cog):

    def __init__(self, bot):
        Post.bot = bot
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        global posts
        await asyncio.sleep(2)
        # noinspection PyTypeChecker
        approve_channel: discord.TextChannel = self.bot.get_channel(main.GLOBAL_CONFIG["APPROVAL_CHANNEL_ID"])
        with open("data/posts.json", "r") as fp:
            posts = [await Post.from_json(q) for q in json.load(fp)]
        for post in posts:
            view = PostApprovalView(post)
            view.message = await approve_channel.fetch_message(post.id)
            self.bot.add_view(view=view, message_id=post.id)
        print("Views have been loaded")


def setup(bot):
    bot.add_cog(PostCog(bot))
