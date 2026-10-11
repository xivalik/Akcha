import asyncio
from contextlib import asynccontextmanager, suppress
from itertools import count

from telegram.error import TelegramError

SPINNER = "🌑🌒🌓🌔🌕🌖🌗🌘"
DOTS = [".", "..", "..."]
FRAME_SECONDS = 1.5  # Telegram limits how often one chat's message can be edited


def frame(text, i):
    return f"{SPINNER[i % len(SPINNER)]} <b>{text}{DOTS[i % len(DOTS)]}</b>"


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
            # A missed frame (e.g. Telegram asking to slow down) doesn't matter
            with suppress(TelegramError):
                await note.edit_text(frame(text, i), parse_mode="HTML")

    task = asyncio.create_task(animate())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        with suppress(TelegramError):
            await note.delete()
