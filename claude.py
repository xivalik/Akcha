import base64

import anthropic
from pydantic import BaseModel

from config import CLAUDE_API

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API)
MODEL = "claude-haiku-5-5"

RECEIPT_PROMPT = """You read photos of shop receipts for an expense tracker.

Most receipts are Finnish. List every purchased item on the receipt:
- name: the product name in the receipt's own language (do not translate), lowercase, keeping
  letters like ä, ö, å. Write cut-off words in full when it's obvious ("ruisleip" -> "ruisleipä").
  No emojis.
- price: the final amount paid for that line as a number, after quantity
  (e.g. "2 x 1,29" -> 2.58). Decimals are often written with a comma: "2,32" means 2.32.

Special lines:
- Discounts (ALENNUS, "-0,50", etc.) belong to the product right above them: subtract the
  discount from that product's price and don't list the discount on its own.
- Bottle/can deposit (PANTTI) is money paid: list it as its own item named "pantti".
- Skip lines that are not products: subtotal, total (YHTEENSÄ), VAT (ALV), payment method
  (KORTTI, PANKKIKORTTI, KÄTEINEN), change (VAIHTORAHA), loyalty bonus/points (BONUS, PLUSSA).

If the image is not a receipt or nothing is readable, return an empty list."""


class ReceiptItem(BaseModel):
    name: str
    price: float


class Receipt(BaseModel):
    items: list[ReceiptItem]


async def read_receipt(image: bytes):
    """Ask Claude for the products on a receipt photo; returns [{"product_name", "price"}]."""
    response = await client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        system=RECEIPT_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",  # Telegram re-encodes photos as JPEG
                            "data": base64.standard_b64encode(image).decode(),
                        },
                    },
                    {"type": "text", "text": "List the products on this receipt."},
                ],
            }
        ],
        output_format=Receipt,
    )
    # A refusal or a cut-off answer has no parsed result
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        return []
    return [
        {"product_name": i.name.strip().lower(), "price": i.price}
        for i in response.parsed_output.items
    ]
