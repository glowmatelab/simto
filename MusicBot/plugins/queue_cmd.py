"""
/queue — show current queue (plain text, no thumbnails)
"""

from pyrogram import filters
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
        return await m.reply_text("❌ Abhi kuch nahi chal raha!", quote=False)

    songs = queue.all_songs(chat_id)
    if not songs:
        return await m.reply_text("📋 Queue empty hai.", quote=False)

    loop_mode = await db.get_loop(chat_id)
    loop_text = {0: "OFF", 1: "🔂 Single", 2: "🔁 Queue"}[loop_mode]
    playing_state = "▶️ Playing" if await db.is_playing(chat_id) else "⏸ Paused"

    lines = [
        f"📋 **Queue** — {playing_state} | Loop: {loop_text}",
        f"Max: {Config.QUEUE_LIMIT} songs\n",
    ]

    for i, song in enumerate(songs):
        prefix = "▶️ Now:" if i == 0 else f"  {i}."
        lines.append(f"{prefix} **{song.title}** `[{song.duration}]` — {song.requester}")

    lines.append(f"\n🎵 {len(songs)}/{Config.QUEUE_LIMIT} songs in queue")

    await m.reply_text("\n".join(lines), quote=False)
