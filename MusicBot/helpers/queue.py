"""
MusicQueue — in-memory queue, capped at Config.QUEUE_LIMIT per group.

Design decisions for Render/storage optimization:
- Pure in-memory: zero DB writes for queue operations
- Hard cap of QUEUE_LIMIT (default 5) songs per group
- Deque for O(1) popleft (next song)
- No file objects stored here — only metadata + file_path string
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional
from config import Config


@dataclass
class Song:
    """Lightweight song object. No PIL images, no thumbnail bytes."""
    id: str            # yt-dlp video id
    title: str
    url: str           # YouTube watch URL
    duration: str      # human-readable "3:45"
    duration_sec: int
    file_path: str = ""
    requester: str = ""
    is_live: bool = False


class MusicQueue:
    def __init__(self):
        # chat_id → deque[Song]
        self._queues: dict[int, deque[Song]] = defaultdict(deque)

    # ── Core ops ──────────────────────────────────────────────────────────────

    def add(self, chat_id: int, song: Song) -> int | None:
        """
        Add song to queue. Returns queue position (1-based) or None if full.
        Position 1 = currently playing, 2 = next, etc.
        """
        q = self._queues[chat_id]
        # Already playing + QUEUE_LIMIT pending = reject
        if len(q) >= Config.QUEUE_LIMIT:
            return None
        q.append(song)
        return len(q)  # 1-based position

    def current(self, chat_id: int) -> Optional[Song]:
        q = self._queues[chat_id]
        return q[0] if q else None

    def next_song(self, chat_id: int) -> Optional[Song]:
        """Pop current, return next (or None if queue is now empty)."""
        q = self._queues[chat_id]
        if q:
            q.popleft()
        return q[0] if q else None

    def peek_next(self, chat_id: int) -> Optional[Song]:
        """Look at next song without removing current."""
        q = self._queues[chat_id]
        return q[1] if len(q) > 1 else None

    def all_songs(self, chat_id: int) -> list[Song]:
        return list(self._queues[chat_id])

    def size(self, chat_id: int) -> int:
        return len(self._queues[chat_id])

    def is_empty(self, chat_id: int) -> bool:
        return len(self._queues[chat_id]) == 0

    def clear(self, chat_id: int):
        self._queues[chat_id].clear()

    def rotate_for_loop(self, chat_id: int):
        """Move current song to end of queue (queue-loop mode)."""
        q = self._queues[chat_id]
        if q:
            q.rotate(-1)
