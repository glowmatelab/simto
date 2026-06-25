# 🎵 MusicBot

Lightweight Telegram music bot — optimized for Render deployment.

## Features
- `/play` — YouTube search + stream audio in VC
- `/pause` `/resume` — playback control
- `/stop` `/end` — stop + leave VC
- `/restart` — replay current song from beginning
- `/loop` — cycle loop modes (off → single → queue)
- `/queue` — view queue (plain text)
- `/ping` — bot status
- `/start` `/help` — info

## Queue Design
- **Max 5 songs per group** (configurable via `QUEUE_LIMIT`)
- Queue is **in-memory only** — zero DB writes for queue operations
- Auto-advances to next song on track end
- Full queue loop and single-track loop supported

## Storage Optimization
- **No thumbnails** — plain text messages only
- Audio files downloaded to `/tmp` (ephemeral on Render)
- Old files auto-cleaned after each track ends
- MongoDB only stores: active calls, loop mode, chat list

## Setup

### 1. Clone and configure
```bash
cp sample.env .env
# Fill in .env values
```

### 2. Get String Session (Pyrogram)
```python
from pyrogram import Client
async with Client("session", api_id=API_ID, api_hash=API_HASH) as c:
    print(await c.export_session_string())
```

### 3. Run locally
```bash
pip install -r requirements.txt
python -m MusicBot
```

### 4. Deploy on Render
- Create a **Web Service** (or **Background Worker**)
- Runtime: **Docker**
- Set all env vars from `sample.env`
- Start command: `python -m MusicBot`

## Environment Variables
| Variable | Required | Default | Description |
|---|---|---|---|
| `API_ID` | ✅ | — | Telegram API ID |
| `API_HASH` | ✅ | — | Telegram API Hash |
| `BOT_TOKEN` | ✅ | — | Bot token from @BotFather |
| `STRING_SESSION` | ✅ | — | Pyrogram user session |
| `OWNER_ID` | ✅ | — | Your Telegram user ID |
| `LOGGER_ID` | ✅ | — | Log group ID |
| `MONGO_URL` | ✅ | — | MongoDB connection string |
| `DURATION_LIMIT_MIN` | ❌ | `60` | Max song duration (minutes) |
| `QUEUE_LIMIT` | ❌ | `5` | Max songs in queue per group |
| `SUPPORT_CHAT` | ❌ | — | Support group link |

## File Structure
```
MusicBot/
├── __init__.py        # Core init (app, userbot, db, queue, call)
├── __main__.py        # Entry point
├── core/
│   ├── bot.py         # Pyrogram Bot client
│   ├── userbot.py     # Pyrogram UserBot client
│   ├── database.py    # MongoDB wrapper
│   └── calls.py       # PyTgCalls wrapper
├── helpers/
│   ├── queue.py       # In-memory queue (5-song cap)
│   └── youtube.py     # yt-dlp search + download
└── plugins/
    ├── play.py        # /play
    ├── controls.py    # /pause /resume /stop /end /restart
    ├── loop.py        # /loop
    ├── queue_cmd.py   # /queue
    └── info.py        # /start /help /ping
```
