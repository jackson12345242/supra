import discord
from config import EMBED_BUILDER_ROLE_ID


def has_embed_role(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    return any(role.id == EMBED_BUILDER_ROLE_ID for role in member.roles)
