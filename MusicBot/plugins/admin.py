"""
Admin commands — Broadcast & Stats
/broadcast user <msg> → all users DM
/broadcast group <msg> → all groups
/stats → total users + groups
"""

import asyncio
import logging

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from MusicBot import app, db
from config import Config

logger = logging.getLogger(__name__)


# ── Broadcast ─────────────────────────────────────────────────────────────────

@app.on_message(filters.command("broadcast") & filters.private & filters.user(Config.OWNER_ID))
async def broadcast_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text(
            "❌ Usage:\n"
            "<code>/broadcast user &lt;message&gt;</code>\n"
            "<code>/broadcast group &lt;message&gt;</code>",
            parse_mode=ParseMode.HTML,
        )

    mode = m.command[1].lower()
    if mode not in ("user", "group"):
        return await m.reply_text(
            "❌ Mode must be <code>user</code> or <code>group</code>.",
            parse_mode=ParseMode.HTML,
        )

    text = " ".join(m.command[2:])
    if not text:
        return await m.reply_text("❌ Message text nahi diya.", parse_mode=ParseMode.HTML)

    status = await m.reply_text("📤 Broadcasting...", parse_mode=ParseMode.HTML)

    if mode == "user":
        ids = await db.get_all_users()
    else:
        ids = await db.get_all_groups()

    success, failed = 0, 0
    for chat_id in ids:
        try:
            await app.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # flood wait se bachne ke liye

    await status.edit_text(
        f"✅ Broadcast done!\n"
        f"<b>Sent:</b> {success}\n"
        f"<b>Failed:</b> {failed}",
        parse_mode=ParseMode.HTML,
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def stats_cmd(_, m: Message):
    total_users = await db.get_user_count()
    total_groups = await db.get_group_count()

    await m.reply_text(
        f"📊 <b>Stats</b>\n\n"
        f"👤 <b>Users:</b> {total_users}\n"
        f"👥 <b>Groups:</b> {total_groups}",
        parse_mode=ParseMode.HTML,
    )
