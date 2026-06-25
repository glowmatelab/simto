"""
/play — search YouTube (py-yt), download via ShruthiBots API, stream in VC.
"""

import asyncio
import logging

from pyrogram import filters
from pyrogram.types import Message

from MusicBot import app, db, queue, call
from MusicBot.helpers.youtube import search_youtube, download_audio
from config import Config

logger = logging.getLogger(__name__)


@app.on_message(filters.command("play") & filters.group)
async def play_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if len(m.command) < 2:
        return await m.reply_text(
            "❌ **Usage:** `/play <song name ya YouTube link>`",
            quote=False,
        )

    query = " ".join(m.command[1:])
    requester = m.from_user.mention if m.from_user else "Unknown"

    status = await m.reply_text(f"🔍 Dhundh raha hoon: **{query}**...", quote=False)

    song = await search_youtube(query)
    if not song:
        return await status.edit_text("❌ Koi result nahi mila. Dobaara try karo.")

    # Duration check
    if not song.is_live and song.duration_sec > Config.DURATION_LIMIT:
        limit_min = Config.DURATION_LIMIT // 60
        return await status.edit_text(
            f"❌ Song bahut lamba hai!\n"
            f"Max limit: **{limit_min} min** | Song: **{song.duration}**"
        )

    song.requester = requester
    chat_id = m.chat.id
    active = await db.get_call(chat_id)

    if not active:
        # VC idle — add to queue and start
        pos = queue.add(chat_id, song)
        if pos is None:
            return await status.edit_text(
                f"❌ Queue full! Max **{Config.QUEUE_LIMIT}** songs.\n"
                f"`/stop` karo ya song khatam hone do."
            )

        await status.edit_text(
            f"⬇️ ShruthiBots se download ho raha hai...\n"
            f"🎵 **{song.title}**"
        )

        song.file_path = await download_audio(song) or ""
        if not song.file_path:
            queue.clear(chat_id)
            return await status.edit_text(
                "❌ Download fail ho gaya.\n"
                "API key check karo ya thodi der baad try karo."
            )

        ok = await call.play(chat_id, song, join_vc=True)
        if not ok:
            queue.clear(chat_id)
            return await status.edit_text(
                "❌ VC join nahi ho paya.\n"
                "Userbot ko group mein admin banao (manage voice chats permission)."
            )

        await status.edit_text(
            f"🎵 **Ab chal raha hai:**\n\n"
            f"🎧 {song.title}\n"
            f"⏱ {song.duration}\n"
            f"👤 Requested by {requester}"
        )

    else:
        # VC active — add to queue
        pos = queue.add(chat_id, song)
        if pos is None:
            return await status.edit_text(
                f"❌ Queue full! Max **{Config.QUEUE_LIMIT}** songs.\n"
                f"`/queue` dekho — `/stop` karo ya wait karo."
            )

        await status.edit_text(
            f"✅ **Queue mein add hua!**\n\n"
            f"🎵 {song.title}\n"
            f"⏱ {song.duration}\n"
            f"📋 Position: **#{pos}**\n"
            f"👤 Requested by {requester}"
        )
