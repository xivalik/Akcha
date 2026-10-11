import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from itertools import count

from telegram.error import RetryAfter, TelegramError

SPINNER = "🌑🌒🌓🌔🌕🌖🌗🌘"
DOTS = [".", "..", "..."]
# Faster than Telegram's ~1 edit/second guideline; if it tells us to slow down,
# the animation stops (see below), so the real answers still get through
FRAME_SECONDS = 0.5


def frame(text, i):
    return f"{SPINNER[i % len(SPINNER)]} <b>{text}{DOTS[i % len(DOTS)]}</b>"


def seconds(retry_after):
    """RetryAfter.retry_after is a number of seconds or a timedelta, depending on settings."""
    if isinstance(retry_after, timedelta):
        return retry_after.total_seconds()
    return retry_after


@asynccontextmanager
async def loading(msg, text):
    """Show an animated "working on it" message while the block runs, then delete it.

    async with loading(msg, "Reading your receipt"):
        ...slow work...
    """
    note = await msg.reply_text(frame(text, 0), parse_mode="HTML")

    async def animate():
        for i in count(1):
            await asyncio.sleep(FRAME_SECONDS)
            try:
                await note.edit_text(frame(text, i), parse_mode="HTML")
            except RetryAfter:
                return  # Telegram asked us to slow down: keep the last frame still
            except TelegramError:
                pass  # a missed frame doesn't matter

    task = asyncio.create_task(animate())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        try:
            await note.delete()
        except RetryAfter as e:
            # Wait as long as Telegram asks; this also spaces out the replies that follow
            await asyncio.sleep(seconds(e.retry_after))
            with suppress(TelegramError):
                await note.delete()
        except TelegramError:
            pass
