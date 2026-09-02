import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int | None
    log_level: str


_token = os.getenv("DISCORD_TOKEN")
if not _token:
    raise RuntimeError("DISCORD_TOKEN is missing. Create a .env file from .env.example.")

_guild_id = os.getenv("GUILD_ID")

settings = Settings(
    token=_token,
    guild_id=int(_guild_id) if _guild_id else None,
    log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
