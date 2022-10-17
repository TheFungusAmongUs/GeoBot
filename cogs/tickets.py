import discord
import main
from utils.enums import TicketStatus


class Ticket:

    def __init__(self, channel: discord.TextChannel, title: str, body: str, author: discord.User, id: int = 0,
                 status: TicketStatus = TicketStatus.OPEN):
        self.author = author
        self.channel = channel
        self.title = title
        self.body = body
        self.id = id
        self.status = status

    def make_embed(self):
        return discord.Embed(
            title=self.title, description=self.body
        ).add_field(name="Ticket Author", value=self.author.mention)

    def to_json(self):
        return dict(self.__dict__.copy(), **{"channel": self.channel.id, "author": self.author.id})

    @classmethod
    async def from_json(cls, json_object: dict, bot: discord.Bot):
        json_object.update(**{"channel": bot.get_channel(json_object["channel"]),
                              "author": await bot.fetch_user(json_object["author"])})
        return cls(**json_object)

    @classmethod
    async def from_modal(cls, title: str, body: str, interaction: discord.Interaction):
        ticket_channel = await cls.create_channel(interaction)
        ticket = cls(ticket_channel, title=title, body=body, author=interaction.user)
        await ticket_channel.send(embed=ticket.make_embed())

        return ticket

    @staticmethod
    async def create_channel(interaction: discord.Interaction) -> discord.TextChannel:
        overwrites = {
            interaction.user: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
        }
        return await interaction.channel.category.create_text_channel(
            name=f"{interaction.user.nick or interaction.user.name}-",
            overwrites=overwrites,
        )

    async def generate_transcript(self) -> tuple[str, list[discord.Attachment]]:
        transcript = ""
        attachments = []
        async for message in self.channel.history():
            transcript += f"{message.author.mention}: {message.content}\n"
            if message.attachments:
                transcript += "Files: "
            for attachment in message.attachments:
                transcript += f"{attachment.filename} "
                attachments += attachment
            transcript += '\n\n'

        return transcript, attachments

    async def close(self):
        pass

    async def reopen(self):
        pass


class TicketStoreView(discord.ui.View):

    def __init__(self, ticket: Ticket):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close-button")
    async def close_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(label="Re-open Ticket", style=discord.ButtonStyle.grey, custom_id="reopen-button")
    async def reopen_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(label="Mark Resolved", style=discord.ButtonStyle.green, custom_id="resolved-button")
    async def resolved_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass


class TicketModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Create a ticket")

        self.add_item(discord.ui.InputText(
            label="Ticket title",
            placeholder="Enter a concise, specific title detailing the problem",
            min_length=10,
            max_length=100
        ))
        self.add_item(discord.ui.InputText(
            label="Ticket Body",
            placeholder="You can elaborate on the problem here",
            min_length=10
        ))

    async def callback(self, interaction: discord.Interaction):
        ticket = await Ticket.from_modal(self.children[0].value, self.children[1].value, interaction)
        ticket_store_channel = interaction.guild.get_channel(main.GLOBAL_CONFIG["TICKET_STORE_CHANNEL_ID"])

        await ticket_store_channel.send(embed=ticket.make_embed())


class TicketCog(discord.Cog):

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(TicketCog(bot))
