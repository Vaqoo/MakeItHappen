import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Always resolve .env relative to the repository, not the process working
# directory. This prevents systemd/restarts from accidentally loading a
# different configuration.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int | None
    log_level: str
    database_url: str


_token = os.getenv("DISCORD_TOKEN", "").strip()
if not _token:
    raise RuntimeError("DISCORD_TOKEN is missing. Set it in the MIH environment.")

_database_url = os.getenv("DATABASE_URL", "").strip()
if not _database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. MIH production requires PostgreSQL/Supabase "
        "so profile, XP, economy and server data survive restarts."
    )

_guild_id = os.getenv("GUILD_ID", "").strip()

settings = Settings(
    token=_token,
    guild_id=int(_guild_id) if _guild_id else None,
    log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    database_url=_database_url,
)
