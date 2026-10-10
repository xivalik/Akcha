import anthropic
from config import CLAUDE_API

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API)
MODEL = "claude-sonnet-5-5"
