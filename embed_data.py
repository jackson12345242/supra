import json
import discord
from storage import read_json, write_json


def _get_all():
    return read_json("embeds", {})


def _save_all(data):
    write_json("embeds", data)


def get_embed_data(guild_id, name):
    return _get_all().get(str(guild_id), {}).get(name)


def set_embed_data(guild_id, name, patch: dict):
    """Shallow-merges `patch` into the stored embed data for (guild_id, name)."""
    all_data = _get_all()
    gid = str(guild_id)
    if gid not in all_data:
        all_data[gid] = {}
    current = all_data[gid].get(name, {})
    current.update(patch)
    all_data[gid][name] = current
    _save_all(all_data)
    return current


def delete_embed_data(guild_id, name):
    all_data = _get_all()
    gid = str(guild_id)
    if gid in all_data and name in all_data[gid]:
        del all_data[gid][name]
    _save_all(all_data)


def list_embeds(guild_id):
    return list(_get_all().get(str(guild_id), {}).keys())


def build_embed_from_data(data: dict) -> discord.Embed:
    embed = discord.Embed()
    if data.get("title"):
        embed.title = data["title"]
    if data.get("description"):
        embed.description = data["description"]
    if data.get("url"):
        embed.url = data["url"]
    if data.get("color"):
        try:
            embed.colour = discord.Colour(int(str(data["color"]).lstrip("#"), 16))
        except (ValueError, TypeError):
            pass
    author = data.get("author") or {}
    if author.get("name"):
        embed.set_author(
            name=author["name"],
            icon_url=author.get("icon_url") or None,
            url=author.get("url") or None,
        )
    footer = data.get("footer") or {}
    if footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)
    if data.get("image"):
        embed.set_image(url=data["image"])
    if data.get("thumbnail"):
        embed.set_thumbnail(url=data["thumbnail"])
    return embed


def to_json_code(data: dict) -> str:
    return json.dumps(data, indent=2)
