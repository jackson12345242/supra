import re
import time

import discord
from config import VOUCH_CHANNEL_ID
from storage import read_json, write_json

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


def setup(bot: discord.Client):
    @bot.event
    async def on_message(message: discord.Message):
        # Ignore the bot's own messages
        if message.author.bot:
            return

        # Only watch the configured vouch channel
        if VOUCH_CHANNEL_ID and message.channel.id != VOUCH_CHANNEL_ID:
            return

        match = VOUCH_RE.match(message.content.strip())
        if not match:
            return

        target_id = int(match.group(1))
        amount = float(match.group(2).replace(",", ""))

        if target_id == message.author.id:
            return await message.reply("You can't vouch for yourself.", mention_author=False)

        record_vouch(message.guild.id, target_id, message.author.id, amount)
        await message.add_reaction("✅")

        # Let other bot.py-level on_message logic (like commands) still run if you add any later
        await bot.process_commands(message)
