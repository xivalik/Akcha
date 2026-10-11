import logging

import anthropic
from telegram.constants import ChatAction

from claude import read_receipt
from db.database import save_translations
from handlers.expenses import is_valid_name, save_and_reply
from handlers.texts import LANGUAGES, t, user_lang

logger = logging.getLogger(__name__)


async def receipt_photo(update, context):
    user = update.effective_user
    msg = update.effective_message
    lang = user_lang(user)
    await msg.reply_chat_action(ChatAction.TYPING)
    # The last photo size is the biggest one
    photo = await msg.photo[-1].get_file()
    image = bytes(await photo.download_as_bytearray())
    try:
        items = await read_receipt(image)
    except anthropic.APIError:
        logger.exception("Reading a receipt failed")
        await msg.reply_text(t(lang, "receipt_failed"))
        return

    # Same rules as typed products: a valid name and a real price
    items = [i for i in items if is_valid_name(i["product_name"]) and i["price"] > 0]
    if not items:
        await msg.reply_text(t(lang, "receipt_empty"))
        return
    # Claude already translated the names; save them so /expenses doesn't ask again
    for code in LANGUAGES:
        translations = {
            i["product_name"]: i["translations"][code]
            for i in items
            if is_valid_name(i["translations"][code])
        }
        if translations:
            save_translations(code, translations)
    # One message per product so each can be undone and retyped on its own
    for item in items:
        shown = item["translations"][lang]
        await save_and_reply(msg, user.id, item, lang, shown if is_valid_name(shown) else None)
