import re
import discord
from discord import app_commands
from storage import read_json, write_json
from embed_data import get_embed_data, build_embed_from_data

CUSTOM_EMOJI_RE = re.compile(r"^<a?:\w+:(\d+)>$")


def parse_emoji_input(raw: str) -> dict:
    match = CUSTOM_EMOJI_RE.match(raw)
    if match:
        return {"id": match.group(1), "raw": raw}
    return {"id": None, "raw": raw}


@app_commands.command(name="reverse-reaction-role", description="Post a message where reacting REMOVES a role instead of adding it")
@app_commands.describe(
    role="Role to remove when a member reacts",
    emoji="Emoji members react with (unicode or custom)",
    embed_name="A saved /embed name to use for the message (optional)",
    channel="Channel to post in (defaults to this channel)",
)
@app_commands.default_permissions(manage_roles=True)
async def reverse_reaction_role(
    interaction: discord.Interaction,
    role: discord.Role,
    emoji: str,
    embed_name: str = None,
    channel: discord.TextChannel = None,
):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)

    target_channel = channel or interaction.channel
    if not isinstance(target_channel, (discord.TextChannel, discord.Thread)):
        return await interaction.response.send_message("Please choose a text channel.", ephemeral=True)

    if role.is_default() or role.managed:
        return await interaction.response.send_message("I can't manage that role.", ephemeral=True)

    if embed_name:
        saved = get_embed_data(interaction.guild_id, embed_name)
        if not saved:
            return await interaction.response.send_message(f"No saved embed named `{embed_name}` was found.", ephemeral=True)
        embed = build_embed_from_data(saved)
    else:
        embed = discord.Embed(
            title="Reverse Reaction Role",
            description=f"React with {emoji} to **remove** the {role.mention} role from yourself.",
            colour=0x0000FF,
        )

    message = await target_channel.send(embed=embed)

    parsed_emoji = parse_emoji_input(emoji)
    try:
        await message.add_reaction(parsed_emoji["raw"])
    except discord.HTTPException:
        await message.delete()
        return await interaction.response.send_message(
            "I couldn't react with that emoji — make sure I have access to it.", ephemeral=True,
        )

    reaction_roles = read_json("reactionroles", {})
    reaction_roles[str(message.id)] = {
        "guild_id": interaction.guild_id,
        "channel_id": target_channel.id,
        "role_id": role.id,
        "emoji": parsed_emoji,
        "reverse": True,
    }
    write_json("reactionroles", reaction_roles)

    await interaction.response.send_message(
        f"Done! Reacting with {emoji} on that message in {target_channel.mention} will now remove {role.mention} from whoever reacts.",
        ephemeral=True,
    )


def setup(bot: discord.Client):
    bot.tree.add_command(reverse_reaction_role)
