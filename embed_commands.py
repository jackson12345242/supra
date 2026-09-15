import discord
from discord import app_commands, ui

from embed_data import (
    get_embed_data,
    set_embed_data,
    build_embed_from_data,
    list_embeds,
    delete_embed_data,
    to_json_code,
)
from permissions import has_embed_role


def _check_role(interaction: discord.Interaction) -> bool:
    return has_embed_role(interaction.user)


async def _deny(interaction: discord.Interaction):
    await interaction.response.send_message(
        "You don't have permission to use the embed builder.", ephemeral=True
    )


def _refresh_embed(interaction: discord.Interaction, name: str) -> discord.Embed:
    data = get_embed_data(interaction.guild_id, name) or {}
    return build_embed_from_data(data)


class BasicInfoModal(ui.Modal, title="Edit Basic Information"):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    embed_title = ui.TextInput(label="Title", required=False, max_length=256)
    description = ui.TextInput(label="Description", required=False, style=discord.TextStyle.paragraph, max_length=2000)
    url = ui.TextInput(label="URL", required=False)
    color = ui.TextInput(label="Color (hex, e.g. FF0000)", required=False, max_length=6)

    async def on_submit(self, interaction: discord.Interaction):
        patch = {
            "title": self.embed_title.value or None,
            "description": self.description.value or None,
            "url": self.url.value or None,
            "color": self.color.value or None,
        }
        set_embed_data(interaction.guild_id, self.name, patch)
        embed = _refresh_embed(interaction, self.name)
        await interaction.response.edit_message(embed=embed)


class AuthorModal(ui.Modal, title="Edit Author"):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    author_name = ui.TextInput(label="Author Name", required=False, max_length=256)
    author_icon = ui.TextInput(label="Author Icon URL", required=False)
    author_url = ui.TextInput(label="Author URL", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        patch = {
            "author": {
                "name": self.author_name.value or None,
                "icon_url": self.author_icon.value or None,
                "url": self.author_url.value or None,
            }
        }
        set_embed_data(interaction.guild_id, self.name, patch)
        embed = _refresh_embed(interaction, self.name)
        await interaction.response.edit_message(embed=embed)


class FooterModal(ui.Modal, title="Edit Footer"):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    footer_text = ui.TextInput(label="Footer Text", required=False, max_length=2048)
    footer_icon = ui.TextInput(label="Footer Icon URL", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        patch = {
            "footer": {
                "text": self.footer_text.value or None,
                "icon_url": self.footer_icon.value or None,
            }
        }
        set_embed_data(interaction.guild_id, self.name, patch)
        embed = _refresh_embed(interaction, self.name)
        await interaction.response.edit_message(embed=embed)


class ImagesModal(ui.Modal, title="Edit Images"):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    image = ui.TextInput(label="Image URL", required=False)
    thumbnail = ui.TextInput(label="Thumbnail URL", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        patch = {
            "image": self.image.value or None,
            "thumbnail": self.thumbnail.value or None,
        }
        set_embed_data(interaction.guild_id, self.name, patch)
        embed = _refresh_embed(interaction, self.name)
        await interaction.response.edit_message(embed=embed)


class EmbedBuilderView(ui.View):
    def __init__(self, name: str):
        super().__init__(timeout=None)
        self.name = name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not _check_role(interaction):
            await _deny(interaction)
            return False
        return True

    @ui.button(label="Edit Basic Information", style=discord.ButtonStyle.primary)
    async def basic_info(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(BasicInfoModal(self.name))

    @ui.button(label="Edit Author", style=discord.ButtonStyle.secondary)
    async def author(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AuthorModal(self.name))

    @ui.button(label="Edit Footer", style=discord.ButtonStyle.secondary)
    async def footer(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(FooterModal(self.name))

    @ui.button(label="Edit Images", style=discord.ButtonStyle.secondary)
    async def images(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ImagesModal(self.name))

    @ui.button(label="Code", style=discord.ButtonStyle.success)
    async def code(self, interaction: discord.Interaction, button: ui.Button):
        data = get_embed_data(interaction.guild_id, self.name) or {}
        code_str = to_json_code(data)
        if len(code_str) > 1900:
            code_str = code_str[:1900] + "\n... (truncated)"
        await interaction.response.send_message(f"```json\n{code_str}\n```", ephemeral=True)


embed_group = app_commands.Group(name="embed", description="Create and manage custom embeds")


@embed_group.command(name="create", description="Start building a new saved embed")
@app_commands.describe(name="A name to save this embed under")
async def embed_create(interaction: discord.Interaction, name: str):
    if not _check_role(interaction):
        return await _deny(interaction)

    set_embed_data(interaction.guild_id, name, {})
    embed = _refresh_embed(interaction, name)
    view = EmbedBuilderView(name)
    await interaction.response.send_message(
        content=(
            "**embed creation**\n"
            "Use the buttons below to customize this embed. You can click the `Code` button "
            f"to copy this embed or use `/embed preview {name}` to show this embed."
        ),
        embed=embed,
        view=view,
    )


@embed_group.command(name="preview", description="Preview a saved embed")
@app_commands.describe(name="The saved embed's name")
async def embed_preview(interaction: discord.Interaction, name: str):
    data = get_embed_data(interaction.guild_id, name)
    if not data:
        return await interaction.response.send_message(f"No saved embed named `{name}`.", ephemeral=True)
    embed = build_embed_from_data(data)
    await interaction.response.send_message(embed=embed)


@embed_group.command(name="post", description="Post a saved embed to a channel")
@app_commands.describe(name="The saved embed's name", channel="Channel to post in (defaults to this channel)")
async def embed_post(interaction: discord.Interaction, name: str, channel: discord.TextChannel = None):
    if not _check_role(interaction):
        return await _deny(interaction)

    data = get_embed_data(interaction.guild_id, name)
    if not data:
        return await interaction.response.send_message(f"No saved embed named `{name}`.", ephemeral=True)

    target = channel or interaction.channel
    embed = build_embed_from_data(data)
    await target.send(embed=embed)
    await interaction.response.send_message(f"Posted `{name}` in {target.mention}.", ephemeral=True)


@embed_group.command(name="list", description="List saved embeds")
async def embed_list(interaction: discord.Interaction):
    names = list_embeds(interaction.guild_id)
    if not names:
        return await interaction.response.send_message("No saved embeds yet.", ephemeral=True)
    await interaction.response.send_message("Saved embeds: " + ", ".join(f"`{n}`" for n in names), ephemeral=True)


@embed_group.command(name="delete", description="Delete a saved embed")
@app_commands.describe(name="The saved embed's name")
async def embed_delete(interaction: discord.Interaction, name: str):
    if not _check_role(interaction):
        return await _deny(interaction)

    delete_embed_data(interaction.guild_id, name)
    await interaction.response.send_message(f"Deleted `{name}`.", ephemeral=True)


def setup(bot: discord.Client):
    bot.tree.add_command(embed_group)
