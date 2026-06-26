"""
Playback controls: /pause /resume /stop /end /restart /skip
"""

import asyncio
import logging

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from MusicBot import app, db, queue, call
from MusicBot.helpers.youtube import download_audio

logger = logging.getLogger(__name__)


async def _require_active(m: Message) -> bool:
    if not await db.get_call(m.chat.id):
        await m.reply_text("❌ Nothing is playing right now.", quote=False)
        return False
    return True


@app.on_message(filters.command("pause") & filters.group)
async def pause_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    if not await db.is_playing(m.chat.id):
        return await m.reply_text("⏸ Already paused.", quote=False)

    ok = await call.pause(m.chat.id)
    if ok:
        await db.set_playing(m.chat.id, False)
        await m.reply_text(
            "<blockquote>⏸ Paused\n› /resume to continue</blockquote>",
            quote=False,
            parse_mode=ParseMode.HTML,
        )
    else:
        await m.reply_text("❌ Failed to pause.", quote=False)


@app.on_message(filters.command("resume") & filters.group)
async def resume_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    if await db.is_playing(m.chat.id):
        return await m.reply_text("▶️ Already playing.", quote=False)

    ok = await call.resume(m.chat.id)
    if ok:
        await db.set_playing(m.chat.id, True)
        song = queue.current(m.chat.id)
        text = "▶️ Resumed"
        if song:
            text += f"\n› {song.title}"
        await m.reply_text(
            f"<blockquote>{text}</blockquote>",
            quote=False,
            parse_mode=ParseMode.HTML,
        )
    else:
        await m.reply_text("❌ Failed to resume.", quote=False)


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
        "<blockquote>⏹ Stopped\n› Queue cleared · Left voice chat</blockquote>",
        quote=False,
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(5)
    try:
        await sent.delete()
    except Exception:
        pass


@app.on_message(filters.command("restart") & filters.group)
async def restart_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if not await _require_active(m):
        return

    song = queue.current(m.chat.id)
    if not song:
        return await m.reply_text("❌ Queue is empty.", quote=False)

    status = await m.reply_text(
        f"<blockquote>🔄 Restarting...\n› {song.title}</blockquote>",
        quote=False,
        parse_mode=ParseMode.HTML,
    )

    if not song.file_path:
        song.file_path = await download_audio(song) or ""

    if not song.file_path:
        return await status.edit_text(
            "❌ File not found. Try /play again.",
            parse_mode=ParseMode.HTML,
        )

    try:
        from pytgcalls.types import AudioQuality, MediaStream
        await call.client.play(
            m.chat.id,
            MediaStream(
                song.file_path,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
            ),
        )
        await db.set_playing(m.chat.id, True)
        await status.edit_text(
            f"<blockquote>🔄 Restarted\n› {song.title}  ·  {song.duration}</blockquote>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await status.edit_text(f"❌ Restart failed: <code>{e}</code>", parse_mode=ParseMode.HTML)


@app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(_, m: Message):
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
            "<blockquote>⏭ Skipped\n› Queue is empty · Left voice chat</blockquote>",
            quote=False,
            parse_mode=ParseMode.HTML,
        )

    status = await m.reply_text(
        "<blockquote>⏭ Skipping...</blockquote>",
        quote=False,
        parse_mode=ParseMode.HTML,
    )

    if not next_song.file_path:
        next_song.file_path = await download_audio(next_song) or ""

    if not next_song.file_path:
        return await status.edit_text(
            f"❌ Download failed: <code>{next_song.title}</code>",
            parse_mode=ParseMode.HTML,
        )

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
            f"<blockquote>⏭ Now Playing\n› {next_song.title}  ·  {next_song.duration}  ·  {next_song.requester}</blockquote>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await status.edit_text(f"❌ Skip failed: <code>{e}</code>", parse_mode=ParseMode.HTML)
