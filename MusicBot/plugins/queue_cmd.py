"""
/queue — show current queue
"""

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from MusicBot import app, db, queue
from config import Config


@app.on_message(filters.command("queue") & filters.group)
async def queue_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    chat_id = m.chat.id

    if not await db.get_call(chat_id):
        return await m.reply_text("❌ Nothing is playing right now.", quote=False)

    songs = queue.all_songs(chat_id)
    if not songs:
        return await m.reply_text("📋 Queue is empty.", quote=False)

    loop_mode = await db.get_loop(chat_id)
    loop_text = {0: "Off", 1: "🔂 Single", 2: "🔁 Queue"}[loop_mode]
    state = "▶️ Playing" if await db.is_playing(chat_id) else "⏸ Paused"

    lines = [f"{state}  ·  Loop: {loop_text}\n"]

    for i, song in enumerate(songs):
        if i == 0:
            lines.append(f"▶️  <b>{song.title}</b>  [{song.duration}]")
        else:
            status = "⚠️" if not song.file_path else f"{i}."
            lines.append(f"{status}  {song.title}  [{song.duration}]  · {song.requester}")

    lines.append(f"\n{len(songs)}/{Config.QUEUE_LIMIT} songs")

    await m.reply_text(
        f"<blockquote>{'<br>'.join(lines)}</blockquote>",
        quote=False,
        parse_mode=ParseMode.HTML,
    )
