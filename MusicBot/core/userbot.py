from kurigram import Client  # pyrogram ki jagah yeh
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
