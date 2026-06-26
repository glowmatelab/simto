"""
/start  /help  /ping
"""

import time
import logging

import psutil
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from MusicBot import app, db, call, boot_time
from config import Config

logger = logging.getLogger(__name__)

# ── Replace with your actual image URLs ───────────────────────────────────────
START_BANNER = "https://drive.google.com/uc?id=15mcuSKZX-1KaTMPhd_R0RT4gRZk_ZEEZ"
HELP_BANNER  = "https://drive.google.com/uc?id=1Ta5EPBa1lg4silBXrwhUENso9eopwoE3"

BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("➕ Add to Group", url="https://t.me/noisefreebot?startgroup=true"),
        InlineKeyboardButton("📢 Updates", url="https://t.me/noisefreemusic"),
    ]
])

HELP_TEXT = """<blockquote>🎵 <b>NoiseFree — Commands</b>

▸ /play &lt;song or link&gt;
▸ /pause  ·  /resume
▸ /stop  ·  /skip  ·  /restart
▸ /loop — off → single → queue
▸ /queue — view current queue
▸ /ping — bot status

⏱ Duration limit: {dl} min
📋 Queue limit: {ql} songs per group</blockquote>"""


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


@app.on_message(filters.command("start"))
async def start_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    if m.chat.type.value == "private":
        await m.reply_photo(
            photo=START_BANNER,
            caption=HELP_TEXT.format(ql=Config.QUEUE_LIMIT, dl=Config.DURATION_LIMIT // 60),
            reply_markup=BUTTONS,
            parse_mode=ParseMode.HTML,
            quote=False,
        )
    else:
        await db.add_chat(m.chat.id)
        await m.reply_photo(
            photo=START_BANNER,
            caption="<blockquote>✅ NoiseFree is ready!\n› Use /play to stream music.</blockquote>",
            reply_markup=BUTTONS,
            parse_mode=ParseMode.HTML,
            quote=False,
        )


@app.on_message(filters.command("help"))
async def help_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    await m.reply_photo(
        photo=HELP_BANNER,
        caption=HELP_TEXT.format(ql=Config.QUEUE_LIMIT, dl=Config.DURATION_LIMIT // 60),
        reply_markup=BUTTONS,
        parse_mode=ParseMode.HTML,
        quote=False,
    )


@app.on_message(filters.command("ping"))
async def ping_cmd(_, m: Message):
    try:
        await m.delete()
    except Exception:
        pass

    t_start = time.time()
    sent = await m.reply_text("🏓 Pinging...", quote=False)
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
        f"<blockquote>🏓 Pong!\n\n"
        f"📡 Latency: <code>{latency} ms</code>\n"
        f"📞 VC Ping: <code>{vc_text}</code>\n"
        f"⏱ Uptime: <code>{uptime}</code>\n"
        f"💾 RAM: <code>{ram}</code>\n"
        f"🖥 CPU: <code>{cpu}%</code>\n"
        f"🎵 Active Groups: <code>{active_chats}</code></blockquote>",
        parse_mode=ParseMode.HTML,
    )
