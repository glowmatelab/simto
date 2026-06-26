"""
Entry point — starts bot + userbot + PyTgCalls.
Run: python -m MusicBot

Render Web Service fix:
  Render expects an HTTP port to be open or it marks the service as failed.
  We run a tiny aiohttp health server on $PORT (default 8080) alongside the bot.
"""

import asyncio
import logging
import os
import signal

from aiohttp import web

from MusicBot import app, userbot, call, db, logger


# ── Health-check HTTP server (for Render) ─────────────────────────────────────

async def _health(request):
    return web.Response(text="OK")


async def start_health_server():
    """Start a minimal HTTP server so Render's port scan succeeds."""
    port = int(os.getenv("PORT", "8080"))
    srv_app = web.Application()
    srv_app.router.add_get("/", _health)
    srv_app.router.add_get("/health", _health)
    runner = web.AppRunner(srv_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ Health server running on port {port}")
    return runner


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    logger.info("🚀 MusicBot starting...")

    # Start health server first so Render marks service as live
    health_runner = await start_health_server()

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
    await health_runner.cleanup()
    logger.info("✅ Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
