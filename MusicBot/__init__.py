"""
MusicBot — lightweight Telegram music streaming bot.
Optimized for Render deployment: minimal memory, no thumbnails, queue-capped.
"""

import asyncio
import logging
import time
from logging.handlers import RotatingFileHandler

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="[%(asctime)s %(levelname)s] %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("musicbot.log", maxBytes=5_000_000, backupCount=2),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
# Silence noisy libs
for _lib in ("httpx", "ntgcalls", "pymongo", "pyrogram", "pytgcalls"):
    logging.getLogger(_lib).setLevel(logging.ERROR)

logger = logging.getLogger("MusicBot")

# ── Config ────────────────────────────────────────────────────────────────────
from config import Config
Config.validate()

# ── Boot time ─────────────────────────────────────────────────────────────────
boot_time: float = time.time()

# ── Pyrogram Bot ──────────────────────────────────────────────────────────────
from MusicBot.core.bot import Bot
app = Bot()

# ── Pyrogram Userbot ──────────────────────────────────────────────────────────
from MusicBot.core.userbot import create_userbot
userbot = create_userbot()

# ── MongoDB ───────────────────────────────────────────────────────────────────
from MusicBot.core.database import Database
db = Database()

# ── In-memory Queue ───────────────────────────────────────────────────────────
from MusicBot.helpers.queue import MusicQueue
queue = MusicQueue()

# ── PyTgCalls handler ─────────────────────────────────────────────────────────
from MusicBot.core.calls import CallManager
call = CallManager()
