from pyrogram import Client  # kurigram hatao
from config import Config


def create_userbot():    # ✅ Original banana
    return Client(
        name="UserBot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        session_string=Config.STRING_SESSION,
        sleep_threshold=30,
        no_updates=False,
    )
