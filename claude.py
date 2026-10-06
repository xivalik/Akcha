import anthropic
from config import CLAUDE_API

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API)

async def ask_claude(text: str) -> str:
    message = await client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": text}],
    )
    return "".join(block.text for block in message.content if block.type == "text")
