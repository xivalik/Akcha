import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from db.database import init_db
from handlers.start import start
from handlers.expenses import expenses, add_product, undo_ask, undo_yes, undo_no
from handlers.admin import admin_panel, send_db
from handlers.receipt import receipt_photo

logging.basicConfig(level=logging.INFO)
# httpx logs every request, and the request URLs contain the bot token
logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("expenses", expenses))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("db", send_db))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_product))
    app.add_handler(MessageHandler(filters.PHOTO, receipt_photo))
    app.add_handler(CallbackQueryHandler(undo_ask, pattern=r"^undo:\d+$"))
    app.add_handler(CallbackQueryHandler(undo_yes, pattern=r"^undo_yes:\d+$"))
    app.add_handler(CallbackQueryHandler(undo_no, pattern=r"^undo_no:\d+$"))
    app.run_polling()


if __name__ == "__main__":
    main()
