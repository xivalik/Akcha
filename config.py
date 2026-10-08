from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API = os.getenv("CLAUDE_API")
