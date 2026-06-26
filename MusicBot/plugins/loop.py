"""
/loop — cycle through loop modes: off → single → queue → off
"""

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from MusicBot import app, db


@app.on_message(filters.command("loop") & filters.group)
async def loop_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    chat_id = m.chat.id
    new_mode = (await db.get_loop(chat_id) + 1) % 3
    await db.set_loop(chat_id, new_mode)

    mode_text = {
        0: "⏹ Loop Off\n› Songs will play once and stop.",
        1: "🔂 Single Loop\n› Current song will repeat.",
        2: "🔁 Queue Loop\n› Entire queue will repeat.",
    }

    await m.reply_text(
        f"<blockquote>{mode_text[new_mode]}</blockquote>",
        quote=False,
        parse_mode=ParseMode.HTML,
    )
