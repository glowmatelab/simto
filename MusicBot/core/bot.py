from pyrogram import Client
from config import Config


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="MusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="MusicBot/plugins"),
            sleep_threshold=30,
        )
