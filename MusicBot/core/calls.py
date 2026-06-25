"""
CallManager — PyTgCalls wrapper.
Stream end → auto-advance queue → cleanup old files.
"""

import asyncio
import logging

from ntgcalls import ConnectionNotFound
from pytgcalls import PyTgCalls, exceptions
from pytgcalls.types import AudioQuality, MediaStream

from config import Config

logger = logging.getLogger(__name__)


class CallManager:
    def __init__(self):
        self._client: PyTgCalls | None = None

    def setup(self, userbot):
        self._client = PyTgCalls(userbot)

        @self._client.on_closed_voice_chat()
        async def _on_end(chat_id: int, _update):
            await self._handle_stream_end(chat_id)

    @property
    def client(self) -> PyTgCalls:
        if not self._client:
            raise RuntimeError("CallManager.setup() not called yet.")
        return self._client

    # ── Stream end ────────────────────────────────────────────────────────────

    async def _handle_stream_end(self, chat_id: int):
        from MusicBot import db, queue, app
        from MusicBot.helpers.youtube import download_audio, cleanup_downloads

        loop_mode = await db.get_loop(chat_id)

        # Single track loop — replay current
        if loop_mode == 1:
            song = queue.current(chat_id)
            if song:
                await self._change_stream(chat_id, song.file_path)
                return

        # Queue loop — rotate and replay
        elif loop_mode == 2:
            queue.rotate_for_loop(chat_id)
            song = queue.current(chat_id)
            if song:
                if not song.file_path:
                    song.file_path = await download_audio(song) or ""
                if song.file_path:
                    await self._change_stream(chat_id, song.file_path)
                    return

        # Normal — advance to next
        next_song = queue.next_song(chat_id)

        if next_song is None:
            # Queue empty — leave VC
            await db.remove_call(chat_id)
            # Keep current songs' files, clean rest
            cleanup_downloads(keep_current_ids=[])
            try:
                await self.client.leave_group_call(chat_id)
            except Exception:
                pass
            try:
                await app.send_message(chat_id, "⏹ Queue khatam — VC se nikal gaya.")
            except Exception:
                pass
            return

        # Download next if needed
        if not next_song.file_path:
            next_song.file_path = await download_audio(next_song) or ""

        if not next_song.file_path:
            try:
                await app.send_message(chat_id, f"❌ Download fail: **{next_song.title}** — skip.")
            except Exception:
                pass
            await self._handle_stream_end(chat_id)
            return

        await self._change_stream(chat_id, next_song.file_path)

        # Clean files not in current queue
        active_ids = [s.id for s in queue.all_songs(chat_id)]
        cleanup_downloads(keep_current_ids=active_ids)

        try:
            await app.send_message(
                chat_id,
                f"🎵 **Ab chal raha hai:**\n\n"
                f"🎧 {next_song.title}\n"
                f"⏱ {next_song.duration}\n"
                f"👤 {next_song.requester}"
            )
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────────

    async def play(self, chat_id: int, song, join_vc: bool = True) -> bool:
        from MusicBot import db, userbot
        from MusicBot.helpers.youtube import download_audio

        if not song.file_path:
            song.file_path = await download_audio(song) or ""
        if not song.file_path:
            return False

        try:
            stream = MediaStream(
                song.file_path,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
            )
            if join_vc:
                try:
                    await self.client.join_group_call(chat_id, stream)
                except exceptions.AlreadyJoinedError:
                    await self.client.change_stream(chat_id, stream)
            else:
                await self.client.change_stream(chat_id, stream)

            await db.set_call(chat_id, userbot.me.id)
            return True
        except Exception as e:
            logger.error(f"Play error [{chat_id}]: {e}")
            return False

    async def _change_stream(self, chat_id: int, file_path: str):
        await self.client.change_stream(
            chat_id,
            MediaStream(
                file_path,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE,
            ),
        )

    async def pause(self, chat_id: int) -> bool:
        try:
            await self.client.pause_stream(chat_id)
            return True
        except (ConnectionNotFound, exceptions.NotInCallError):
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            await self.client.resume_stream(chat_id)
            return True
        except (ConnectionNotFound, exceptions.NotInCallError):
            return False

    async def stop(self, chat_id: int) -> bool:
        from MusicBot import db, queue
        from MusicBot.helpers.youtube import cleanup_downloads

        queue.clear(chat_id)
        await db.remove_call(chat_id)
        cleanup_downloads(keep_current_ids=[])

        try:
            await self.client.leave_group_call(chat_id)
        except Exception:
            pass
        return True

    async def ping(self) -> float:
        try:
            return await self.client.ping
        except Exception:
            return 0.0
