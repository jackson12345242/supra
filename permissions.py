import os
from dotenv import load_dotenv

load_dotenv()

EMBED_BUILDER_ROLE_ID = int(os.getenv("EMBED_BUILDER_ROLE_ID", 0))
VOUCH_CHANNEL_ID = int(os.getenv("VOUCH_CHANNEL_ID", 0))
