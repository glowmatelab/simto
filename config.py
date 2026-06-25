from os import getenv
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Telegram Credentials ──────────────────────────────────────────────
    API_ID: int = int(getenv("API_ID", "0"))
    API_HASH: str = getenv("API_HASH", "")

    # ── Bot & Userbot ─────────────────────────────────────────────────────
    BOT_TOKEN: str = getenv("BOT_TOKEN", "")
    STRING_SESSION: str = getenv("STRING_SESSION", "")

    # ── Owner & Logger ────────────────────────────────────────────────────
    OWNER_ID: int = int(getenv("OWNER_ID", "0"))
    LOGGER_ID: int = int(getenv("LOGGER_ID", "0"))

    # ── MongoDB ───────────────────────────────────────────────────────────
    MONGO_URL: str = getenv("MONGO_URL", "")

    # ── ShruthiBots API ───────────────────────────────────────────────────
    YOUTUBE_API_URL: str = getenv("YOUTUBE_API_URL", "https://api.shrutibots.site")
    SHRUTI_API_KEY: str = getenv("SHRUTI_API_KEY", "")

    # ── Music Limits ──────────────────────────────────────────────────────
    DURATION_LIMIT: int = int(getenv("DURATION_LIMIT_MIN", "60")) * 60
    QUEUE_LIMIT: int = int(getenv("QUEUE_LIMIT", "5"))

    # ── Support ───────────────────────────────────────────────────────────
    SUPPORT_CHAT: str = getenv("SUPPORT_CHAT", "https://t.me/+0000000000000000")

    @classmethod
    def validate(cls):
        missing = []
        for var, val in {
            "API_ID": cls.API_ID,
            "API_HASH": cls.API_HASH,
            "BOT_TOKEN": cls.BOT_TOKEN,
            "STRING_SESSION": cls.STRING_SESSION,
            "OWNER_ID": cls.OWNER_ID,
            "LOGGER_ID": cls.LOGGER_ID,
            "MONGO_URL": cls.MONGO_URL,
            "SHRUTI_API_KEY": cls.SHRUTI_API_KEY,
        }.items():
            if not val or (isinstance(val, int) and val == 0):
                missing.append(var)
        if missing:
            raise SystemExit(
                f"❌ Missing env vars: {', '.join(missing)}\n"
                "Please set them in your .env file."
            )
