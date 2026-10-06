from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
from config import TOKEN
from handlers.basic import start, echo
from handlers.fun import roll, claude

logging.basicConfig(level=logging.INFO)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("claude", claude))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == "__main__":
    main()