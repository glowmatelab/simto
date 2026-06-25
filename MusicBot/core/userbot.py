# from pyrogram import Client  →  change to:
from kurigram import Client
from config import Config


class UserBot(Client):
    def __init__(self):
        super().__init__(
            name="UserBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.STRING_SESSION,
            sleep_threshold=30,
            no_updates=False,
        )
