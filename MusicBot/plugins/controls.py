"""
Playback controls: /pause /resume /stop /end /restart /skip
"""

import asyncio
import logging

from pyrogram import filters
from pyrogram.types import Message

from MusicBot import app, db, queue, call
from MusicBot.helpers.youtube import download_audio

logger = logging.getLogger(__name__)


async def _require_active(m: Message) -> bool:
    """Returns True if there's an active call, else sends error and returns False."""
    if not await db.get_call(m.chat.id):
        await m.reply_text("❌ Abhi kuch nahi chal raha!", quote=False)
        return False
    return True


# ── /pause ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("pause") & filters.group)
async def pause_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    if not await db.is_playing(m.chat.id):
        return await m.reply_text("⏸ Pehle se pause hai!", quote=False)

    ok = await call.pause(m.chat.id)
    if ok:
        await db.set_playing(m.chat.id, False)
        await m.reply_text(
            f"⏸ **Pause kar diya**\n"
            f"Resume karne ke liye: /resume",
            quote=False,
        )
    else:
        await m.reply_text("❌ Pause nahi ho paya.", quote=False)


# ── /resume ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command("resume") & filters.group)
async def resume_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    if await db.is_playing(m.chat.id):
        return await m.reply_text("▶️ Pehle se chal raha hai!", quote=False)

    ok = await call.resume(m.chat.id)
    if ok:
        await db.set_playing(m.chat.id, True)
        song = queue.current(m.chat.id)
        text = "▶️ **Resume ho gaya!**"
        if song:
            text += f"\n🎵 {song.title}"
        await m.reply_text(text, quote=False)
    else:
        await m.reply_text("❌ Resume nahi ho paya.", quote=False)


# ── /stop & /end ──────────────────────────────────────────────────────────────

@app.on_message(filters.command(["stop", "end"]) & filters.group)
async def stop_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    await call.stop(m.chat.id)

    sent = await m.reply_text(
        "⏹ **Playback band kar diya.**\n"
        "Queue clear ho gayi. VC chhod diya.",
        quote=False,
    )
    await asyncio.sleep(5)
    try:
        await sent.delete()
    except Exception:
        pass


# ── /restart ──────────────────────────────────────────────────────────────────

@app.on_message(filters.command("restart") & filters.group)
async def restart_cmd(_, m: Message):
    """Restart the current song from beginning."""
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    song = queue.current(m.chat.id)
    if not song:
        return await m.reply_text("❌ Queue empty hai!", quote=False)

    status = await m.reply_text(f"🔄 **Restart kar raha hoon:** {song.title}", quote=False)

    if not song.file_path:
        song.file_path = await download_audio(song) or ""

    if not song.file_path:
        return await status.edit_text("❌ File nahi mili. /play dobara try karo.")

    try:
        from pytgcalls.types import AudioQuality, MediaStream
        await call.client.play(  # Fixed: change_stream → play
            m.chat.id,
            MediaStream(
                song.file_path,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
            ),
        )
        await db.set_playing(m.chat.id, True)
        await status.edit_text(
            f"🔄 **Restart hua!**\n"
            f"🎵 {song.title}\n"
            f"⏱ {song.duration}"
        )
    except Exception as e:
        await status.edit_text(f"❌ Restart fail: {e}")


# ── /skip ─────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(_, m: Message):
    """Skip current song and play next in queue."""
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    next_song = queue.next_song(m.chat.id)

    if next_song is None:
        await call.stop(m.chat.id)
        return await m.reply_text(
            "⏭ **Skip kar diya!**\n"
            "Queue mein aur koi song nahi — VC chhod diya.",
            quote=False,
        )

    status = await m.reply_text(f"⏭ **Skip kar raha hoon...**", quote=False)

    if not next_song.file_path:
        next_song.file_path = await download_audio(next_song) or ""

    if not next_song.file_path:
        await status.edit_text(f"❌ Next song download nahi hua: **{next_song.title}** — dobara try karo.")
        return

    try:
        from pytgcalls.types import AudioQuality, MediaStream
        await call.client.play(
            m.chat.id,
            MediaStream(
                next_song.file_path,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
            ),
        )
        await db.set_playing(m.chat.id, True)
        await status.edit_text(
            f"⏭ **Skip! Ab chal raha hai:**\n\n"
            f"🎧 {next_song.title}\n"
            f"⏱ {next_song.duration}\n"
            f"👤 {next_song.requester}"
        )
    except Exception as e:
        await status.edit_text(f"❌ Skip fail: {e}")
