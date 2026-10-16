import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
