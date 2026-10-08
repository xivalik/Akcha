from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
from config import TOKEN
from db.database import init_db
from handlers.start import start
from handlers.expenses import expenses, add_product_request

logging.basicConfig(level=logging.INFO)


def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("expenses", expenses))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_request)
    )
    app.run_polling()


if __name__ == "__main__":
    main()
