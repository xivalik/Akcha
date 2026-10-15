import logging

import anthropic

from claude import read_receipt
from handlers.expenses import is_valid_name, save_and_reply
from handlers.loading import loading
from handlers.texts import t

logger = logging.getLogger(__name__)


async def receipt_photo(update, context):
    msg = update.effective_message
    try:
        async with loading(msg, t("reading_receipt")):
            # The last photo size is the biggest one
            photo = await msg.photo[-1].get_file()
            image = bytes(await photo.download_as_bytearray())
            items = await read_receipt(image)
    except anthropic.APIError:
        logger.exception("Reading a receipt failed")
        await msg.reply_text(t("receipt_failed"))
        return

    # Same rules as typed products: a valid name and a real price
    items = [i for i in items if is_valid_name(i["product_name"]) and i["price"] > 0]
    if not items:
        await msg.reply_text(t("receipt_empty"))
        return
    # One message per product so each can be undone and retyped on its own
    for item in items:
        await save_and_reply(msg, update.effective_user.id, item)
