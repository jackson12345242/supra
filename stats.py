import discord
from discord import app_commands
from storage import read_json
from formatting import fmt_amount


@app_commands.command(name="stats", description="View a member's vouch stats")
@app_commands.describe(user="User to check (defaults to you)")
async def stats(interaction: discord.Interaction, user: discord.User = None):
    if not interaction.guild:
        return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)

    target = user or interaction.user
    vouches = read_json("vouches", {})
    record = vouches.get(str(interaction.guild_id), {}).get("users", {}).get(str(target.id))

    embed = discord.Embed(colour=0x0000FF)
    embed.set_author(name=target.name, icon_url=target.display_avatar.url)
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    if not record or record["count"] == 0:
        embed.description = "No vouches recorded yet."
    else:
        embed.add_field(name="Total Vouched", value=fmt_amount(record["total"]), inline=True)
        embed.add_field(name="Deal Count", value=str(record["count"]), inline=True)
        recent = list(reversed(record["deals"][-5:]))
        if recent:
            lines = [
                f"<@{d['from']}> — {fmt_amount(d['amount'])} <t:{d['timestamp'] // 1000}:R>"
                for d in recent
            ]
            embed.add_field(name="Recent Deals", value="\n".join(lines), inline=False)

    await interaction.response.send_message(embed=embed)


def setup(bot: discord.Client):
    bot.tree.add_command(stats)
