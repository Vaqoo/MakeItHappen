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
                automod_mentions INTEGER NOT NULL DEFAULT 0,
                welcome_channel_id INTEGER,
                welcome_enabled INTEGER NOT NULL DEFAULT 0,
                goodbye_channel_id INTEGER,
                goodbye_enabled INTEGER NOT NULL DEFAULT 0,
                suggestion_channel_id INTEGER,
                suggestion_enabled INTEGER NOT NULL DEFAULT 0,
                anti_raid_enabled INTEGER NOT NULL DEFAULT 0,
                raid_threshold INTEGER NOT NULL DEFAULT 8,
                raid_window INTEGER NOT NULL DEFAULT 20,
                lockdown_enabled INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, title TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT);
            CREATE TABLE IF NOT EXISTS user_stats (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, xp INTEGER NOT NULL DEFAULT 0, streak INTEGER NOT NULL DEFAULT 0, last_daily TEXT, last_work TEXT, PRIMARY KEY (guild_id, user_id));
            CREATE TABLE IF NOT EXISTS achievements (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, achievement TEXT NOT NULL, earned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (guild_id, user_id, achievement));
            CREATE TABLE IF NOT EXISTS profiles (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, display_name TEXT NOT NULL DEFAULT '', bio TEXT NOT NULL DEFAULT '', favorite_quote TEXT NOT NULL DEFAULT '', favorite_color TEXT NOT NULL DEFAULT 'purple', title TEXT NOT NULL DEFAULT '', banner_url TEXT NOT NULL DEFAULT '', showcase TEXT NOT NULL DEFAULT '', PRIMARY KEY (guild_id, user_id));
            CREATE TABLE IF NOT EXISTS moods (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, mood TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, entry TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS wins (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, win TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS economy (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, coins INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (guild_id, user_id));
            CREATE TABLE IF NOT EXISTS inventory (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, item_id TEXT NOT NULL, purchased_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (guild_id, user_id, item_id));
            CREATE TABLE IF NOT EXISTS birthdays (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, month INTEGER NOT NULL, day INTEGER NOT NULL, PRIMARY KEY (guild_id, user_id));
            CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, moderator_id INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            """
        )
        migrations = {
            "guild_config": {
                "welcome_channel_id": "INTEGER", "welcome_enabled": "INTEGER NOT NULL DEFAULT 0",
                "goodbye_channel_id": "INTEGER", "goodbye_enabled": "INTEGER NOT NULL DEFAULT 0",
                "suggestion_channel_id": "INTEGER", "suggestion_enabled": "INTEGER NOT NULL DEFAULT 0",
                "anti_raid_enabled": "INTEGER NOT NULL DEFAULT 0", "raid_threshold": "INTEGER NOT NULL DEFAULT 8",
                "raid_window": "INTEGER NOT NULL DEFAULT 20", "lockdown_enabled": "INTEGER NOT NULL DEFAULT 0",
            },
            "user_stats": {"last_work": "TEXT"},
            "profiles": {
                "favorite_color": "TEXT NOT NULL DEFAULT 'purple'", "title": "TEXT NOT NULL DEFAULT ''",
                "banner_url": "TEXT NOT NULL DEFAULT ''", "showcase": "TEXT NOT NULL DEFAULT ''",
            },
        }
        for table, columns in migrations.items():
            existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
            for name, definition in columns.items():
                if name not in existing:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def ensure_guild(guild_id: int) -> None:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,))


def get_config(guild_id: int) -> sqlite3.Row:
    ensure_guild(guild_id)
    with _connect() as db:
        return db.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)).fetchone()


def set_config(guild_id: int, field: str, value: int | None) -> None:
    allowed = {"log_channel_id", "temp_voice_channel_id", "temp_voice_category_id", "automod_enabled", "automod_links", "automod_invites", "automod_caps", "automod_mentions", "welcome_channel_id", "welcome_enabled", "goodbye_channel_id", "goodbye_enabled", "suggestion_channel_id", "suggestion_enabled", "anti_raid_enabled", "raid_threshold", "raid_window", "lockdown_enabled"}
    if field not in allowed:
        raise ValueError("Invalid config field")
    ensure_guild(guild_id)
    with _connect() as db:
        db.execute(f"UPDATE guild_config SET {field} = ? WHERE guild_id = ?", (value, guild_id))


def add_xp(guild_id: int, user_id: int, amount: int) -> int:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        db.execute("UPDATE user_stats SET xp = MAX(0, xp + ?) WHERE guild_id = ? AND user_id = ?", (amount, guild_id, user_id))
        return int(db.execute("SELECT xp FROM user_stats WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()["xp"])


def get_stats(guild_id: int, user_id: int) -> sqlite3.Row:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        return db.execute("SELECT * FROM user_stats WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def set_daily(guild_id: int, user_id: int, day: str, streak: int) -> None:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        db.execute("UPDATE user_stats SET last_daily = ?, streak = ? WHERE guild_id = ? AND user_id = ?", (day, streak, guild_id, user_id))


def set_last_work(guild_id: int, user_id: int, timestamp: str) -> None:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO user_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        db.execute("UPDATE user_stats SET last_work = ? WHERE guild_id = ? AND user_id = ?", (timestamp, guild_id, user_id))


def add_goal(guild_id: int, user_id: int, title: str) -> int:
    with _connect() as db:
        return int(db.execute("INSERT INTO goals (guild_id, user_id, title) VALUES (?, ?, ?)", (guild_id, user_id, title)).lastrowid)


def get_goals(guild_id: int, user_id: int, include_completed: bool = False):
    with _connect() as db:
        query = "SELECT * FROM goals WHERE guild_id = ? AND user_id = ?" + ("" if include_completed else " AND completed_at IS NULL") + " ORDER BY id DESC"
        return db.execute(query, (guild_id, user_id)).fetchall()


def complete_goal(guild_id: int, user_id: int, goal_id: int) -> bool:
    with _connect() as db:
        return db.execute("UPDATE goals SET completed_at = CURRENT_TIMESTAMP WHERE id = ? AND guild_id = ? AND user_id = ? AND completed_at IS NULL", (goal_id, guild_id, user_id)).rowcount > 0


def delete_goal(guild_id: int, user_id: int, goal_id: int) -> bool:
    with _connect() as db:
        return db.execute("DELETE FROM goals WHERE id = ? AND guild_id = ? AND user_id = ?", (goal_id, guild_id, user_id)).rowcount > 0


def award(guild_id: int, user_id: int, achievement: str) -> bool:
    with _connect() as db:
        return db.execute("INSERT OR IGNORE INTO achievements (guild_id, user_id, achievement) VALUES (?, ?, ?)", (guild_id, user_id, achievement)).rowcount > 0


def get_achievements(guild_id: int, user_id: int):
    with _connect() as db:
        return db.execute("SELECT achievement, earned_at FROM achievements WHERE guild_id = ? AND user_id = ? ORDER BY earned_at DESC", (guild_id, user_id)).fetchall()


def get_profile(guild_id: int, user_id: int) -> sqlite3.Row:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO profiles (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        return db.execute("SELECT * FROM profiles WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def set_profile(guild_id: int, user_id: int, display_name: str | None = None, bio: str | None = None, favorite_quote: str | None = None, favorite_color: str | None = None, title: str | None = None, banner_url: str | None = None, showcase: str | None = None) -> None:
    current = get_profile(guild_id, user_id)
    values = (display_name if display_name is not None else current["display_name"], bio if bio is not None else current["bio"], favorite_quote if favorite_quote is not None else current["favorite_quote"], favorite_color if favorite_color is not None else current["favorite_color"], title if title is not None else current["title"], banner_url if banner_url is not None else current["banner_url"], showcase if showcase is not None else current["showcase"])
    values = tuple(str(v)[:500] for v in values)
    with _connect() as db:
        db.execute("UPDATE profiles SET display_name = ?, bio = ?, favorite_quote = ?, favorite_color = ?, title = ?, banner_url = ?, showcase = ? WHERE guild_id = ? AND user_id = ?", (*values, guild_id, user_id))


def add_mood(guild_id: int, user_id: int, mood: str, note: str = "") -> None:
    with _connect() as db:
        db.execute("INSERT INTO moods (guild_id, user_id, mood, note) VALUES (?, ?, ?, ?)", (guild_id, user_id, mood, note[:500]))


def get_moods(guild_id: int, user_id: int, limit: int = 10):
    with _connect() as db:
        return db.execute("SELECT * FROM moods WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT ?", (guild_id, user_id, limit)).fetchall()


def add_journal(guild_id: int, user_id: int, entry: str) -> int:
    with _connect() as db:
        return int(db.execute("INSERT INTO journal (guild_id, user_id, entry) VALUES (?, ?, ?)", (guild_id, user_id, entry[:2000])).lastrowid)


def get_journal(guild_id: int, user_id: int, limit: int = 5):
    with _connect() as db:
        return db.execute("SELECT * FROM journal WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT ?", (guild_id, user_id, limit)).fetchall()


def add_win(guild_id: int, user_id: int, win: str) -> int:
    with _connect() as db:
        return int(db.execute("INSERT INTO wins (guild_id, user_id, win) VALUES (?, ?, ?)", (guild_id, user_id, win[:500])).lastrowid)


def get_wins(guild_id: int, user_id: int, limit: int = 10):
    with _connect() as db:
        return db.execute("SELECT * FROM wins WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT ?", (guild_id, user_id, limit)).fetchall()


def get_leaderboard(guild_id: int, limit: int = 10):
    with _connect() as db:
        return db.execute("SELECT user_id, xp, streak FROM user_stats WHERE guild_id = ? ORDER BY xp DESC LIMIT ?", (guild_id, limit)).fetchall()


def get_rank(guild_id: int, user_id: int) -> int:
    xp = get_stats(guild_id, user_id)["xp"]
    with _connect() as db:
        return int(db.execute("SELECT COUNT(*) + 1 FROM user_stats WHERE guild_id = ? AND xp > ?", (guild_id, xp)).fetchone()[0])


def add_warning(guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
    with _connect() as db:
        return int(db.execute("INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)", (guild_id, user_id, moderator_id, reason[:500])).lastrowid)


def get_warnings(guild_id: int, user_id: int):
    with _connect() as db:
        return db.execute("SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id DESC", (guild_id, user_id)).fetchall()


def clear_warnings(guild_id: int, user_id: int) -> int:
    with _connect() as db:
        return db.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).rowcount


def get_economy(guild_id: int, user_id: int) -> sqlite3.Row:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO economy (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        return db.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def add_coins(guild_id: int, user_id: int, amount: int) -> int:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO economy (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        db.execute("UPDATE economy SET coins = MAX(0, coins + ?) WHERE guild_id = ? AND user_id = ?", (amount, guild_id, user_id))
        return int(db.execute("SELECT coins FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()["coins"])


def buy_item(guild_id: int, user_id: int, item_id: str, price: int) -> bool:
    with _connect() as db:
        db.execute("INSERT OR IGNORE INTO economy (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        if db.execute("SELECT 1 FROM inventory WHERE guild_id = ? AND user_id = ? AND item_id = ?", (guild_id, user_id, item_id)).fetchone():
            return False
        coins = int(db.execute("SELECT coins FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()["coins"])
        if coins < price:
            return False
        db.execute("UPDATE economy SET coins = coins - ? WHERE guild_id = ? AND user_id = ?", (price, guild_id, user_id))
        db.execute("INSERT INTO inventory (guild_id, user_id, item_id) VALUES (?, ?, ?)", (guild_id, user_id, item_id))
        return True


def get_inventory(guild_id: int, user_id: int):
    with _connect() as db:
        return db.execute("SELECT item_id, purchased_at FROM inventory WHERE guild_id = ? AND user_id = ? ORDER BY purchased_at DESC", (guild_id, user_id)).fetchall()


def set_birthday(guild_id: int, user_id: int, month: int, day: int) -> None:
    with _connect() as db:
        db.execute("INSERT INTO birthdays (guild_id, user_id, month, day) VALUES (?, ?, ?, ?) ON CONFLICT(guild_id, user_id) DO UPDATE SET month=excluded.month, day=excluded.day", (guild_id, user_id, month, day))


def get_birthday(guild_id: int, user_id: int):
    with _connect() as db:
        return db.execute("SELECT * FROM birthdays WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def get_birthdays(guild_id: int, month: int, day: int):
    with _connect() as db:
        return db.execute("SELECT user_id FROM birthdays WHERE guild_id = ? AND month = ? AND day = ?", (guild_id, month, day)).fetchall()
