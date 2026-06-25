"""
YouTube helper — search via py-yt, download via ShruthiBots API.

ShruthiBots API endpoints used:
  GET /download?url=<video_id>&type=audio|video&api_key=<key>  → streams file
  GET /live?url=<video_id>&type=live&api_key=<key>             → returns {stream_url}

Search is done locally via py-yt (VideosSearch) — no API call needed for that.
Downloads are done via ShruthiBots API — their server does the heavy lifting,
so Render ka IP ban nahi hoga YouTube se.
"""

import asyncio
import glob
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiohttp
from py_yt import VideosSearch, Playlist

from config import Config

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory search cache — avoids repeated API calls for same query
_search_cache: dict[str, tuple] = {}   # key → (Song, timestamp)
_CACHE_TTL = 600  # 10 min

# Semaphore — max 3 simultaneous downloads (API rate limit consideration)
_download_sem = asyncio.Semaphore(3)


@dataclass
class Song:
    """Lightweight song object — no thumbnail bytes, no PIL."""
    id: str
    title: str
    url: str
    duration: str        # "3:45"
    duration_sec: int
    file_path: str = ""
    requester: str = ""
    is_live: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_duration(duration: Optional[str]) -> tuple[str, int]:
    """Return (human_str, total_seconds) from yt duration string like '3:45'."""
    if not duration or duration == "LIVE":
        return ("LIVE", 0)
    parts = duration.split(":")
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            h, m, s = 0, int(parts[0]), int(parts[1])
        else:
            return (duration, 0)
        return (duration, h * 3600 + m * 60 + s)
    except Exception:
        return (duration, 0)


def _find_local_file(video_id: str, video: bool = False) -> Optional[str]:
    """Check if file already downloaded locally."""
    audio_exts = {".m4a", ".webm", ".opus", ".mp3", ".ogg"}
    video_exts = {".mp4", ".mkv", ".mov"}
    want = video_exts if video else audio_exts

    candidates = sorted(glob.glob(f"{DOWNLOAD_DIR}/{video_id}*"))
    for path in candidates:
        if any(path.endswith(e) for e in (".part", ".ytdl", ".info.json", ".temp")):
            continue
        if Path(path).suffix.lower() in want:
            return path
    # fallback: any file with that id
    for path in candidates:
        if not any(path.endswith(e) for e in (".part", ".ytdl", ".info.json", ".temp")):
            return path
    return None


# ── Search ────────────────────────────────────────────────────────────────────

async def search_youtube(query: str) -> Optional[Song]:
    """
    Search YouTube using py-yt (local, no API key needed).
    Results cached for 10 min to save repeated lookups.
    """
    loop = asyncio.get_running_loop()
    cache_key = query.lower().strip()
    now = loop.time()

    # Check cache
    if cache_key in _search_cache:
        cached_song, ts = _search_cache[cache_key]
        if now - ts < _CACHE_TTL:
            logger.debug(f"Search cache hit: {query}")
            return Song(**{**cached_song.__dict__, "file_path": "", "requester": ""})

    try:
        search = VideosSearch(query, limit=1)
        results = await search.next()
    except Exception as e:
        logger.error(f"YT search error for '{query}': {e}")
        return None

    if not results or not results.get("result"):
        return None

    data = results["result"][0]
    raw_duration = data.get("duration")
    is_live = raw_duration is None or raw_duration == "LIVE"
    dur_str, dur_sec = _fmt_duration(raw_duration)

    song = Song(
        id=data.get("id", ""),
        title=data.get("title", "Unknown")[:80],
        url=data.get("link", ""),
        duration=dur_str,
        duration_sec=dur_sec,
        is_live=is_live,
    )

    # Cache it
    _search_cache[cache_key] = (song, now)
    # Keep cache size in check
    if len(_search_cache) > 150:
        oldest = min(_search_cache, key=lambda k: _search_cache[k][1])
        del _search_cache[oldest]

    return song


# ── Download via ShruthiBots API ──────────────────────────────────────────────

async def download_audio(song: Song, video: bool = False) -> Optional[str]:
    """
    Download via ShruthiBots API.
    - Their server fetches from YouTube (their IP, not Render's)
    - We just stream the response to disk
    - Returns local file path or None on failure
    """
    if song.is_live:
        return await _get_live_url(song.video_id if hasattr(song, 'video_id') else song.id)

    # Check if already downloaded
    existing = _find_local_file(song.id, video)
    if existing and os.path.getsize(existing) > 1000:
        logger.info(f"Local cache hit: {song.id}")
        return existing

    async with _download_sem:
        return await _api_download(song.id, video)


async def _api_download(video_id: str, video: bool = False) -> Optional[str]:
    """Hit ShruthiBots /download endpoint and save to disk."""
    file_type = "video" if video else "audio"
    ext = "mp4" if video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
    tmp_path = file_path + ".part"

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "url": video_id,
                "type": file_type,
                "api_key": Config.SHRUTI_API_KEY,
            }
            async with session.get(
                f"{Config.YOUTUBE_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    logger.error(f"ShruthiBots API error: HTTP {resp.status} for {video_id}")
                    return None

                with open(tmp_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):  # 128KB chunks
                        f.write(chunk)

        # Rename only if download complete
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1000:
            os.rename(tmp_path, file_path)
            logger.info(f"✅ Downloaded via ShruthiBots: {video_id}.{ext}")
            return file_path
        else:
            logger.error(f"Downloaded file empty: {video_id}")
            _safe_remove(tmp_path)
            return None

    except asyncio.TimeoutError:
        logger.error(f"Timeout downloading {video_id}")
        _safe_remove(tmp_path)
        return None
    except Exception as e:
        logger.error(f"Download error {video_id}: {e}")
        _safe_remove(tmp_path)
        return None


async def _get_live_url(video_id: str) -> Optional[str]:
    """Get live stream URL via ShruthiBots /live endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "url": video_id,
                "type": "live",
                "api_key": Config.SHRUTI_API_KEY,
            }
            async with session.get(
                f"{Config.YOUTUBE_API_URL}/live",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    url = data.get("stream_url")
                    if url:
                        return url
    except Exception as e:
        logger.warning(f"Live URL fetch failed for {video_id}: {e}")

    # Fallback: direct YouTube URL (may or may not work)
    return f"https://www.youtube.com/watch?v={video_id}"


# ── Cleanup ───────────────────────────────────────────────────────────────────

def cleanup_downloads(keep_current_ids: list[str] = None):
    """
    Delete downloaded files NOT in keep_current_ids.
    Called after each track ends to keep disk near zero on Render.
    """
    keep = set(keep_current_ids or [])
    try:
        for fname in os.listdir(DOWNLOAD_DIR):
            fpath = os.path.join(DOWNLOAD_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            # Extract video_id (filename = <id>.ext)
            vid_id = Path(fname).stem
            if vid_id not in keep and not fname.endswith(".part"):
                _safe_remove(fpath)
                logger.debug(f"Cleaned: {fname}")
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")


def _safe_remove(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
