from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
import logging

import anthropic

from claude import english_names
from config import BOT_TOKEN
from db.database import init_db, old_product_names, rename_products
from handlers.start import start
from handlers.expenses import (
    expenses,
    add_product_request,
    is_valid_name,
    undo_ask,
    undo_keep,
    undo_add,
)
from handlers.admin import admin_panel, send_db
from handlers.receipt import receipt_photo

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def products_to_english(app):
    """Products saved before the bot was English only can be in any language:
    rename them once to their English names. If Claude can't be reached, try next start."""
    old = old_product_names()
    if old is None:
        return
    names, english = old
    missing = [n for n in names if n not in english]
    if missing:
        try:
            english |= await english_names(missing)
        except anthropic.APIError:
            logger.exception("Renaming old products to English failed")
            return
    rename_products({n: e for n, e in english.items() if is_valid_name(e)})


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(products_to_english).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("expenses", expenses))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("db", send_db))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_request)
    )
    app.add_handler(MessageHandler(filters.PHOTO, receipt_photo))
    app.add_handler(CallbackQueryHandler(undo_ask, pattern=r"^undo:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(undo_add, pattern=r"^undo_yes:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(undo_keep, pattern=r"^undo_no:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(send_db, pattern=r"^admin:db$"))
    app.run_polling()


if __name__ == "__main__":
    main()
