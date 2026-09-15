import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Modules that expose a setup(bot) function to register their app_commands
EXTENSION_MODULES = [
    "reverse_reaction_role",
    "stats",
    "permissions",
    "embed_data",
]


def load_extensions():
    for module_name in EXTENSION_MODULES:
        try:
            module = __import__(module_name)
            if hasattr(module, "setup"):
                module.setup(bot)
                log.info(f"Loaded {module_name}")
            else:
                log.info(f"{module_name} has no setup(bot), skipping command registration")
        except Exception as e:
            log.warning(f"Could not load {module_name}: {e}")


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    load_extensions()

    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        log.error(f"Command sync failed: {e}")


# --- Reverse reaction role handling ---
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    from storage import read_json  # local import avoids circulars at startup

    if payload.user_id == bot.user.id:
        return

    reaction_roles = read_json("reactionroles", {})
    entry = reaction_roles.get(str(payload.message_id))
    if not entry or not entry.get("reverse"):
        return

    guild = bot.get_guild(entry["guild_id"])
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    role = guild.get_role(entry["role_id"])
    if member and role:
        try:
            await member.remove_roles(role, reason="Reverse reaction role")
        except discord.Forbidden:
            log.warning(f"Missing permissions to remove role {role.id} from {member.id}")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is not set in the environment.")
    bot.run(TOKEN)
