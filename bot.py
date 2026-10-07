from telegram.ext import Application, CommandHandler
import logging
from config import TOKEN
from db.database import init_db
from handlers.basic import start

logging.basicConfig(level=logging.INFO)

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()