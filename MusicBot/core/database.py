"""
Database — MongoDB wrapper.
Only stores what music streaming actually needs:
  - active_calls   : which groups are in a VC call right now
  - loop           : loop mode per group (0=off, 1=single, 2=queue)
  - chats          : groups the bot is in (for /broadcast etc.)
All queues are kept in-memory (MusicQueue) — no DB writes for queue items.
"""

import logging
from pymongo import AsyncMongoClient
from config import Config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self._client = AsyncMongoClient(
            Config.MONGO_URL,
            serverSelectionTimeoutMS=10_000,
            connectTimeoutMS=15_000,
            socketTimeoutMS=15_000,
            maxPoolSize=10,        # Render free tier: keep it low
            minPoolSize=2,
            maxIdleTimeMS=20_000,
            retryWrites=True,
        )
        self._db = self._client.MusicBotDB

        # Collections
        self._calls = self._db.active_calls   # {chat_id, playing, assistant_id}
        self._loop  = self._db.loop_modes     # {chat_id, mode}
        self._chats = self._db.chats          # {chat_id}

        # In-memory caches (reduce DB round-trips)
        self._call_cache: dict[int, dict] = {}   # chat_id → {playing, assistant_id}
        self._loop_cache: dict[int, int]  = {}   # chat_id → loop_mode

    # ── Connection ────────────────────────────────────────────────────────────

    async def connect(self):
        try:
            await self._client.admin.command("ping")
            logger.info("✅ MongoDB connected")
        except Exception as e:
            raise SystemExit(f"❌ MongoDB connection failed: {e}")

    async def close(self):
        self._client.close()

    # ── Active Calls ──────────────────────────────────────────────────────────

    async def set_call(self, chat_id: int, assistant_id: int):
        """Mark a group as having an active VC call."""
        data = {"playing": True, "assistant_id": assistant_id}
        self._call_cache[chat_id] = data
        await self._calls.update_one(
            {"chat_id": chat_id},
            {"$set": {**data, "chat_id": chat_id}},
            upsert=True,
        )

    async def get_call(self, chat_id: int) -> dict | None:
        """Return call info dict if group has active call, else None."""
        if chat_id in self._call_cache:
            return self._call_cache[chat_id]
        doc = await self._calls.find_one({"chat_id": chat_id})
        if doc:
            self._call_cache[chat_id] = {"playing": doc["playing"], "assistant_id": doc["assistant_id"]}
            return self._call_cache[chat_id]
        return None

    async def set_playing(self, chat_id: int, playing: bool):
        """Toggle playing/paused state."""
        if chat_id in self._call_cache:
            self._call_cache[chat_id]["playing"] = playing
        await self._calls.update_one({"chat_id": chat_id}, {"$set": {"playing": playing}})

    async def is_playing(self, chat_id: int) -> bool:
        """True if not paused."""
        info = await self.get_call(chat_id)
        return bool(info and info.get("playing", False))

    async def remove_call(self, chat_id: int):
        """Remove active call entry (stream ended / stopped)."""
        self._call_cache.pop(chat_id, None)
        await self._calls.delete_one({"chat_id": chat_id})

    # ── Loop Mode ─────────────────────────────────────────────────────────────

    async def get_loop(self, chat_id: int) -> int:
        """0=off, 1=single track, 2=entire queue."""
        if chat_id in self._loop_cache:
            return self._loop_cache[chat_id]
        doc = await self._loop.find_one({"chat_id": chat_id})
        mode = doc["mode"] if doc else 0
        self._loop_cache[chat_id] = mode
        return mode

    async def set_loop(self, chat_id: int, mode: int):
        self._loop_cache[chat_id] = mode
        await self._loop.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "mode": mode}},
            upsert=True,
        )

    # ── Chats Registry ────────────────────────────────────────────────────────

    async def add_chat(self, chat_id: int):
        await self._chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id}},
            upsert=True,
        )

    async def get_all_chats(self) -> list[int]:
        return [doc["chat_id"] async for doc in self._chats.find({}, {"chat_id": 1})]
