import logging

import anthropic

from claude import read_receipt
from handlers.expenses import is_valid_name, save_and_reply

logger = logging.getLogger(__name__)


async def receipt_photo(update, context):
    msg = update.effective_message
    # The last photo size is the biggest one
    photo = await msg.photo[-1].get_file()
    image = bytes(await photo.download_as_bytearray())
    try:
        products = await read_receipt(image)
    except anthropic.APIError:
        logger.exception("Reading a receipt failed")
        await msg.reply_text(
            "Sorry, I couldn't read the receipt right now. Please try again later."
        )
        return

    # Skip what Claude misread: names a typed product couldn't have, and prices of 0 or less
    products = [(name, price) for name, price in products if is_valid_name(name) and price > 0]
    if not products:
        await msg.reply_text(
            "I couldn't find any products on this photo. Try a clearer photo of the receipt."
        )
        return
    # One message per product so each can be undone and retyped on its own
    for name, price in products:
        await save_and_reply(msg, update.effective_user.id, name, price)
