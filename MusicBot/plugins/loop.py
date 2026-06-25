"""
/loop — cycle through loop modes: off → single → queue → off
"""

from pyrogram import filters
from pyrogram.types import Message

from MusicBot import app, db


@app.on_message(filters.command("loop") & filters.group)
async def loop_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    chat_id = m.chat.id
    current = await db.get_loop(chat_id)

    # Cycle: 0 → 1 → 2 → 0
    new_mode = (current + 1) % 3
    await db.set_loop(chat_id, new_mode)

    mode_text = {
        0: "➡️ **Loop OFF**\nSongs ek baar bajenge aur queue aage badh jaayegi.",
        1: "🔂 **Loop: Single Track**\nCurrent song baar baar bajega.",
        2: "🔁 **Loop: Queue**\nPoori queue loop hogi.",
    }

    await m.reply_text(mode_text[new_mode], quote=False)
