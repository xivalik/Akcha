from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API = os.getenv("CLAUDE_API")