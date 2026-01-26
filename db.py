import sqlite3
import re
from pathlib import Path
import discord
import logging
logger = logging.getLogger("robort")

__all__ = ["set_channel", "get_channel"]


def _sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name)


def _db_path_for_guild(guild: discord.Guild) -> Path:
    name = _sanitize_name(guild.name)
    filename = f"{name}_{guild.id}.db"
    dir_path = Path.cwd() / "guild"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / filename


def _ensure_db(guild: discord.Guild):
    db_path = _db_path_for_guild(guild)
    with sqlite3.connect(db_path) as conn:
        try:
            cur = conn.cursor()
                
            cur.execute('PRAGMA journal_mode=WAL;')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()
            logger.info("Initialized DB for guild %s at %s", guild.id, db_path)
        except sqlite3.Error as e:
            logger.error("Error initializing database for guild %s: %s", guild.id, e)


def set_channel(guild: discord.Guild, channel_id: int, channel_type: str = "pin_channel"):
    _ensure_db(guild)
    db_path = _db_path_for_guild(guild)
    with sqlite3.connect(db_path) as conn: 
        try:
            cur = conn.cursor()
            cur.execute('REPLACE INTO settings (key, value) VALUES (?, ?)', (channel_type, str(channel_id)))
            conn.commit()
            logger.info("Set %s for guild %s to channel ID %s", channel_type, guild.id, channel_id)
        except sqlite3.Error as e:
            logger.error("Error setting %s for guild %s: %s", channel_type, guild.id, e)


def get_channel(guild: discord.Guild, channel_type: str = "pin_channel"):
    db_path = _db_path_for_guild(guild)
    if not db_path.exists():
        logger.warning("DB for guild %s does not exist when getting %s", guild.id, channel_type)
        return None
    with sqlite3.connect(db_path) as conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT value FROM settings WHERE key = ?', (channel_type,))
            row = cur.fetchone()
        except sqlite3.Error as e:
            logger.error("Error getting %s for guild %s: %s", channel_type, guild.id, e)
            return None
    return int(row[0]) if row else None
