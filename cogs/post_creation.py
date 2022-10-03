import discord
import main
from cogs.post import PostModal
from utils.enums import PostType


class CreatePostView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Post", emoji="📝", style=discord.ButtonStyle.green, custom_id="create-post")
    async def create_post_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PostModal(PostType.FEEDBACK_QUESTION))

    @discord.ui.button(label="Create Bug Report", emoji="🪲", style=discord.ButtonStyle.red, custom_id="create-bug")
    async def create_bug_report_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(PostModal(PostType.BUG_REPORT))


class PostCreationCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        create_post_channel: discord.TextChannel = self.bot.get_channel(
            main.GLOBAL_CONFIG["CREATE_POST_CHANNEL_ID"]
        )
        if not await create_post_channel.history().flatten():
            embed = discord.Embed(
                title="Create Post/Bug Report",
                description="You can create a post or bug report by clicking on the respective button below :)\n\n"
                            "Feel free to give your feedback or ask any questions,"
                            " just make sure it's on topic and constructive!"
            ).set_footer(text="Any images can be added once the post has been approved!")
            await create_post_channel.send(embed=embed, view=CreatePostView())
        else:
            self.bot.add_view(CreatePostView())


def setup(bot):
    bot.add_cog(PostCreationCog(bot))