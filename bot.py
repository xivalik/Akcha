from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
import logging
from config import BOT_TOKEN
from db.database import init_db
from handlers.start import start
from handlers.expenses import expenses, add_product_request, undo_add

logging.basicConfig(level=logging.INFO)


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("expenses", expenses))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_request)
    )
    app.add_handler(CallbackQueryHandler(undo_add, pattern=r"^undo:\d+:\d+$"))
    app.run_polling()


if __name__ == "__main__":
    main()
