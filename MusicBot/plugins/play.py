"""
/play — search YouTube, download, stream in VC.
"""

import logging

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant, ChatAdminRequired, PeerIdInvalid
from pyrogram.types import Message

from MusicBot import app, db, queue, call, userbot
from MusicBot.helpers.youtube import search_youtube, download_audio
from config import Config

logger = logging.getLogger(__name__)


async def _ensure_assistant_in_group(m: Message) -> bool:
    chat_id = m.chat.id

    try:
        member = await app.get_chat_member(chat_id, userbot.me.id)
        if member.status in (ChatMemberStatus.BANNED, ChatMemberStatus.RESTRICTED):
            await m.reply_text(
                "❌ Assistant is banned in this group.\nPlease unban and try again.",
                quote=False,
            )
            return False
        return True
    except UserNotParticipant:
        pass
    except Exception:
        return True

    try:
        await m.reply_text(
            f"⏳ Adding <code>@{userbot.me.username}</code> to the group...",
            quote=False,
            parse_mode=ParseMode.HTML,
        )
        await app.add_chat_members(chat_id, userbot.me.id)
        return True
    except UserAlreadyParticipant:
        return True
    except ChatAdminRequired:
        await m.reply_text(
            f"❌ Make the bot an admin so it can add <code>@{userbot.me.username}</code>.",
            quote=False,
            parse_mode=ParseMode.HTML,
        )
        return False
    except PeerIdInvalid:
        await m.reply_text(
            f"❌ Please add <code>@{userbot.me.username}</code> to the group manually.",
            quote=False,
            parse_mode=ParseMode.HTML,
        )
        return False
    except Exception as e:
        logger.error(f"Failed to add assistant to {chat_id}: {e}")
        await m.reply_text(
            f"❌ Please add <code>@{userbot.me.username}</code> to the group manually.",
            quote=False,
            parse_mode=ParseMode.HTML,
        )
        return False


@app.on_message(filters.command("play") & filters.group)
async def play_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if len(m.command) < 2:
        return await m.reply_text(
            "❌ Usage: <code>/play &lt;song name or YouTube link&gt;</code>",
            quote=False,
            parse_mode=ParseMode.HTML,
        )

    query = " ".join(m.command[1:])
    first_name = m.from_user.first_name if m.from_user else "Unknown"

    assistant_ok = await _ensure_assistant_in_group(m)
    if not assistant_ok:
        return

    status = await m.reply_text(
        f"🔍 <blockquote>{query}</blockquote>",
        quote=False,
        parse_mode=ParseMode.HTML,
    )

    song = await search_youtube(query)
    if not song:
        return await status.edit_text(
            "❌ No results found. Please try again.",
            parse_mode=ParseMode.HTML,
        )

    if not song.is_live and song.duration_sec > Config.DURATION_LIMIT:
        limit_min = Config.DURATION_LIMIT // 60
        return await status.edit_text(
            f"❌ Song exceeds the duration limit of {limit_min} min.",
            parse_mode=ParseMode.HTML,
        )

    song.requester = first_name
    chat_id = m.chat.id
    active = await db.get_call(chat_id)

    if not active:
        pos = queue.add(chat_id, song)
        if pos is None:
            return await status.edit_text(
                f"❌ Queue is full! Max {Config.QUEUE_LIMIT} songs.",
                parse_mode=ParseMode.HTML,
            )

        await status.edit_text(
            f"🎵 <blockquote>{song.title}\n› Downloading...</blockquote>",
            parse_mode=ParseMode.HTML,
        )

        song.file_path = await download_audio(song) or ""
        if not song.file_path:
            queue.clear(chat_id)
            return await status.edit_text(
                "❌ Download failed. Please try again.",
                parse_mode=ParseMode.HTML,
            )

        ok = await call.play(chat_id, song, join_vc=True)
        if not ok:
            queue.clear(chat_id)
            return await status.edit_text(
                "❌ Failed to join voice chat.\n"
                "Make sure the assistant has Manage Voice Chats permission.",
                parse_mode=ParseMode.HTML,
            )

        await status.edit_text(
            f"🎵 sᴄᴀɴɴɪɴɢ . . .<blockquote>{song.title}\n› {song.duration} · {first_name}</blockquote>",
            parse_mode=ParseMode.HTML,
        )

    else:
        pos = queue.add(chat_id, song)
        if pos is None:
            return await status.edit_text(
                f"❌ Queue is full! Max {Config.QUEUE_LIMIT} songs.",
                parse_mode=ParseMode.HTML,
            )

        await status.edit_text(
            f"🎵 ɴᴏᴡ ᴘʟᴀʏɪɴɢ <blockquote>{song.title}\n› #{pos} · {first_name}</blockquote>",
            parse_mode=ParseMode.HTML,
        )
