import discord

import main


class Ticket:

    def __init__(self, channel: discord.TextChannel, title: str, body: str, author: discord.User, id: int = 0):
        self.author = author
        self.channel = channel
        self.title = title
        self.body = body
        self.id: int = id

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
        overwrites = {
            interaction.user: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
        }
        ticket_channel: discord.TextChannel = (
            await interaction.channel.category.create_text_channel(
                name=f"{interaction.user.nick or interaction.user.name}-",
                overwrites=overwrites,
            )
        )

        ticket = cls(ticket_channel, title=title, body=body, author=interaction.user)
        await ticket_channel.send(embed=ticket.make_embed())

        return ticket


class TicketStoreView(discord.ui.View):

    def __init__(self, ticket: Ticket):
        super().__init__(timeout=None)


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
