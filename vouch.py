import re
import time

import discord
from config import VOUCH_CHANNEL_ID
from storage import read_json, write_json
from formatting import fmt_amount

VOUCH_RE = re.compile(r"^vouch\s+<@!?(\d+)>\s+\$?([\d,]+(?:\.\d+)?)\s*(.*)$", re.IGNORECASE)


def record_vouch(guild_id: int, vouched_user_id: int, from_user_id: int, amount: float):
    vouches = read_json("vouches", {})
    gid = str(guild_id)
    uid = str(vouched_user_id)

    guild_data = vouches.setdefault(gid, {"users": {}})
    record = guild_data["users"].setdefault(uid, {"count": 0, "total": 0, "deals": []})

    record["count"] += 1
    record["total"] += amount
    record["deals"].append({
        "from": from_user_id,
        "amount": amount,
        "timestamp": int(time.time() * 1000),
    })

    write_json("vouches", vouches)
    return record


def build_vouch_embed(guild: discord.Guild, vouched_user: discord.abc.User, from_user: discord.abc.User, amount: float, record: dict) -> discord.Embed:
    embed = discord.Embed(
        title="Supraa's Stocks",
        colour=0x0000FF,
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(
        name="Vouch Format",
        value="`vouch @user $amount`",
        inline=False,
    )
    embed.add_field(
        name="Total Transacted",
        value=fmt_amount(record["total"]),
        inline=False,
    )
    embed.set_footer(text=f"Vouched by {from_user.name} for {vouched_user.name}")

    return embed


def setup(bot: discord.Client):
    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if VOUCH_CHANNEL_ID and message.channel.id != VOUCH_CHANNEL_ID:
            return

        match = VOUCH_RE.match(message.content.strip())
        if not match:
            return

        target_id = int(match.group(1))
        amount = float(match.group(2).replace(",", ""))

        if target_id == message.author.id:
            return await message.reply("You can't vouch for yourself.", mention_author=False)

        target_user = message.guild.get_member(target_id) or await bot.fetch_user(target_id)

        record = record_vouch(message.guild.id, target_id, message.author.id, amount)

        embed = build_vouch_embed(message.guild, target_user, message.author, amount, record)
        await message.reply(embed=embed, mention_author=False)

        await bot.process_commands(message)
