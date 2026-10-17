import base64

import anthropic
from pydantic import BaseModel

from config import CLAUDE_API_KEY

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)
MODEL = "claude-haiku-5-5"

NAMING = """Name each product the way you'd write it on a shopping list: the general kind \
of product in English, lowercase, usually 1-2 words. Drop brands, sizes, flavours and \
packaging. Prices of products with the same name get added up, so always use the same \
name for the same kind of product.
Examples: "valio rasvaton maito 1l" -> "milk", "cola sokton 1,5l" -> "cola", \
"mansikka puikko 10 kpl" -> "ice cream", "pantti" -> "deposit"."""

RECEIPT_PROMPT = f"""You read photos of (mostly Finnish) shop receipts for an expense tracker.
List every purchased item with its final price: multiply quantities, subtract any discount \
from the item above it, and read "2,32" as 2.32. Bottle deposits (PANTTI) count as items. \
Skip totals, VAT, payment, change and bonus lines. If it's not a readable receipt, return \
no items.

{NAMING}"""

NAME_PROMPT = f"The user typed a product name for an expense tracker.\n\n{NAMING}"


class Item(BaseModel):
    name: str
    price: float


class Receipt(BaseModel):
    items: list[Item]


class Name(BaseModel):
    name: str


async def ask(system, content, schema, effort):
    r = await client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": effort},
        system=system,
        messages=[{"role": "user", "content": content}],
        output_format=schema,
    )
    # A refusal or cut-off answer has no parsed result
    return r.parsed_output if r.stop_reason == "end_turn" else None


async def read_receipt(image: bytes):
    """Return [(name, price)] for the products on a receipt photo."""
    img = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",  # Telegram re-encodes photos as JPEG
            "data": base64.standard_b64encode(image).decode(),
        },
    }
    out = await ask(RECEIPT_PROMPT, [img], Receipt, "medium")
    return [(i.name.strip().lower(), i.price) for i in out.items] if out else []


async def english_name(name):
    """Return the short English name of a typed product, or None."""
    out = await ask(NAME_PROMPT, name, Name, "low")
    return out.name.strip().lower() if out else None
