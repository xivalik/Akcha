from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API = os.getenv("CLAUDE_API")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # your Telegram user id
