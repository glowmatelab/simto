"""
Entry point — starts bot + userbot + PyTgCalls.
Run: python -m MusicBot
"""

import asyncio
import logging
import signal

from MusicBot import app, userbot, call, db, logger


async def main():
    logger.info("🚀 MusicBot starting...")

    # Connect to MongoDB
    await db.connect()

    # Start userbot
    await userbot.start()
    logger.info(f"✅ Userbot ready: @{userbot.me.username}")

    # Wire PyTgCalls to userbot
    call.setup(userbot)
    await call.client.start()
    logger.info("✅ PyTgCalls ready")

    # Start bot
    await app.start()
    logger.info(f"✅ Bot ready: @{app.me.username}")
    logger.info("🎵 MusicBot is live!")

    # Keep alive until signal
    stop_event = asyncio.Event()

    def _shutdown(sig, frame):
        logger.info(f"⚡ Signal {sig} received — shutting down...")
        asyncio.get_event_loop().call_soon_threadsafe(stop_event.set)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _shutdown)

    await stop_event.wait()

    # Graceful shutdown
    logger.info("🛑 Stopping MusicBot...")
    try:
        await call.client.stop()
    except Exception:
        pass
    try:
        await userbot.stop()
    except Exception:
        pass
    try:
        await app.stop()
    except Exception:
        pass
    await db.close()
    logger.info("✅ Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
