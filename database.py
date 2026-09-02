import sqlite3
from pathlib import Path

DB_PATH = Path("data/makeithappen.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                log_channel_id INTEGER,
                temp_voice_channel_id INTEGER,
                temp_voice_category_id INTEGER,
                automod_enabled INTEGER NOT NULL DEFAULT 0,
                automod_links INTEGER NOT NULL DEFAULT 0,
                automod_invites INTEGER NOT NULL DEFAULT 1,
                automod_caps INTEGER NOT NULL DEFAULT 0,
                automod_mentions INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS user_stats (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                last_daily TEXT,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS achievements (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                achievement TEXT NOT NULL,
                earned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, achievement)
            );
            """
        )


def ensure_guild(guild_id: int) -> None:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,))


def get_config(guild_id: int) -> sqlite3.Row:
    ensure_guild(guild_id)
    with _connect() as db:
        return db.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)).fetchone()


def set_config(guild_id: int, field: str, value: int | None) -> None:
    allowed = {
        "log_channel_id", "temp_voice_channel_id", "temp_voice_category_id",
        "automod_enabled", "automod_links", "automod_invites", "automod_caps", "automod_mentions",
    }
    if field not in allowed:
        raise ValueError("Invalid config field")
    ensure_guild(guild_id)
    with _connect() as db:
        db.execute(f"UPDATE guild_config SET {field} = ? WHERE guild_id = ?", (value, guild_id))


def add_xp(guild_id: int, user_id: int, amount: int) -> int:
    ensure_guild(guild_id)
    with _connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        db.execute(
            "UPDATE user_stats SET xp = xp + ? WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id),
        )
        row = db.execute(
            "SELECT xp FROM user_stats WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
        return int(row["xp"])


def get_stats(guild_id: int, user_id: int) -> sqlite3.Row:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        return db.execute(
            "SELECT * FROM user_stats WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def set_daily(guild_id: int, user_id: int, day: str, streak: int) -> None:
    with _connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        db.execute(
            "UPDATE user_stats SET last_daily = ?, streak = ? WHERE guild_id = ? AND user_id = ?",
            (day, streak, guild_id, user_id),
        )


def add_goal(guild_id: int, user_id: int, title: str) -> int:
    with _connect() as db:
        cursor = db.execute(
            "INSERT INTO goals (guild_id, user_id, title) VALUES (?, ?, ?)",
            (guild_id, user_id, title),
        )
        return int(cursor.lastrowid)


def get_goals(guild_id: int, user_id: int, include_completed: bool = False):
    with _connect() as db:
        query = "SELECT * FROM goals WHERE guild_id = ? AND user_id = ?"
        params: list[object] = [guild_id, user_id]
        if not include_completed:
            query += " AND completed_at IS NULL"
        query += " ORDER BY id DESC"
        return db.execute(query, params).fetchall()


def complete_goal(guild_id: int, user_id: int, goal_id: int) -> bool:
    with _connect() as db:
        cursor = db.execute(
            "UPDATE goals SET completed_at = CURRENT_TIMESTAMP WHERE id = ? AND guild_id = ? AND user_id = ? AND completed_at IS NULL",
            (goal_id, guild_id, user_id),
        )
        return cursor.rowcount > 0


def award(guild_id: int, user_id: int, achievement: str) -> bool:
    with _connect() as db:
        cursor = db.execute(
            "INSERT OR IGNORE INTO achievements (guild_id, user_id, achievement) VALUES (?, ?, ?)",
            (guild_id, user_id, achievement),
        )
        return cursor.rowcount > 0


def get_achievements(guild_id: int, user_id: int):
    with _connect() as db:
        return db.execute(
            "SELECT achievement, earned_at FROM achievements WHERE guild_id = ? AND user_id = ? ORDER BY earned_at DESC",
            (guild_id, user_id),
        ).fetchall()
