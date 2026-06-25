"""
/start  /help  /ping
Plain text only — no images, no thumbnails.
"""

import time
import logging

import psutil
from pyrogram import filters
from pyrogram.types import Message

from MusicBot import app, db, call, boot_time
from config import Config

logger = logging.getLogger(__name__)

HELP_TEXT = """
🎵 **MusicBot — Commands**

**Playback**
`/play <song/link>` — YouTube se gaana bajao
`/pause` — Pause karo
`/resume` — Resume karo
`/stop` or `/end` — Band karo aur VC chhor do
`/restart` — Current song dobara suru karo
`/loop` — Loop mode change karo (off → single → queue)

**Info**
`/queue` — Queue dekho (max {ql} songs)
`/ping` — Bot ka status dekho
`/help` — Yeh message

**Notes**
• Queue me max **{ql}** songs ek group me
• Duration limit: **{dl} min** per song
• Loop modes: off / single track / full queue
""".strip()


def _human_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


# ── /start ────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("start"))
async def start_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if m.chat.type.value == "private":
        await m.reply_text(
            f"👋 **MusicBot me aapka swagat hai!**\n\n"
            f"Mujhe apne group me add karo aur `/play` se gaane bajao.\n\n"
            + HELP_TEXT.format(ql=Config.QUEUE_LIMIT, dl=Config.DURATION_LIMIT // 60),
            quote=False,
        )
    else:
        # Register chat in DB
        await db.add_chat(m.chat.id)
        await m.reply_text(
            "✅ **MusicBot ready hai!**\nGaana bajane ke liye: `/play <song name>`",
            quote=False,
        )


# ── /help ─────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("help"))
async def help_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    await m.reply_text(
        HELP_TEXT.format(ql=Config.QUEUE_LIMIT, dl=Config.DURATION_LIMIT // 60),
        quote=False,
    )


# ── /ping ─────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("ping"))
async def ping_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    t_start = time.time()
    sent = await m.reply_text("🏓 Ping...", quote=False)
    latency = round((time.time() - t_start) * 1000, 1)

    uptime = _human_time(int(time.time() - boot_time))

    mem = psutil.virtual_memory()
    ram = f"{mem.used / 1024**3:.1f}GB / {mem.total / 1024**3:.1f}GB"
    cpu = psutil.cpu_percent(interval=0.3)

    active_chats = len(await db.get_all_chats())

    try:
        vc_ping = round(await call.ping(), 1)
        vc_text = f"{vc_ping} ms"
    except Exception:
        vc_text = "N/A"

    await sent.edit_text(
        f"🏓 **Pong!**\n\n"
        f"📡 Latency: `{latency} ms`\n"
        f"📞 VC Ping: `{vc_text}`\n"
        f"⏱ Uptime: `{uptime}`\n"
        f"💾 RAM: `{ram}`\n"
        f"🖥 CPU: `{cpu}%`\n"
        f"🎵 Active Groups: `{active_chats}`"
    )
