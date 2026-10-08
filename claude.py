import json

import anthropic
from config import CLAUDE_API

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API)
MODEL = "claude-sonnet-5-5"


async def ask_claude(text: str) -> str:
    message = await client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": text}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


PARSE_PROMPT = """Extract every purchase (product and price) from the user's message for an expense tracker.
Messages are informal and can be written any way - read them as a person would.
- product_name: correctly spelled, capitalized, singular, in the user's language.
- price: a plain number, with shorthand expanded (k = thousand). A lone number next to a product is its price.
If there is no purchase with a price, return an empty list."""

# Claude is forced to reply with JSON that matches this shape
PURCHASES_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "price": {"type": "number"},
                },
                "required": ["product_name", "price"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


async def parse_purchases(text: str) -> list[dict]:
    """Return [{"product_name": "Apple", "price": 3.0}, ...] or [] if nothing found."""
    message = await client.beta.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=PARSE_PROMPT,
        messages=[{"role": "user", "content": text}],
        output_config={
            "effort": "low",  # simple task: keep it fast and cheap
            "format": {"type": "json_schema", "schema": PURCHASES_SCHEMA},
        },
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if this model declines, the API retries on another model
    )
    if message.stop_reason != "end_turn":  # refused or cut off
        return []
    text_block = next(b.text for b in message.content if b.type == "text")
    return json.loads(text_block)["items"]
