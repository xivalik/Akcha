import base64
import json

import anthropic
from pydantic import BaseModel

from config import CLAUDE_API

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API)
MODEL = "claude-haiku-5-5"


NAMING_RULES = """- Always write the name in English, whatever language it is in ("maito" -> "milk",
  "ruisleipä" -> "rye bread", "молоко" -> "milk").
- Name what the product is, the way you'd write it on a shopping list: the general kind of
  product, usually one or two words ("energiajuoma 0,473l tlk" -> "energy drink",
  "talouspaperi dry&strong 4rl" -> "kitchen paper", "mandariini nadorcott" -> "mandarin").
- Leave out brands, sizes, weights, pack counts, packaging, varieties, colours, flavours and
  extras like "sugar-free" or "salted" ("omena punainen 1 kg" -> "apple",
  "cola sokton 1,5l" -> "cola", "valio rasvaton maito" -> "milk").
- Think about what the item really is, not just its words: "mansikka puikko 10 kpl" is a box
  of ice cream bars -> "ice cream"; "fazer sininen" -> "chocolate".
- The same kind of product always gets the same name, so their prices can be added up.
- Bottle and can deposits (pantti) are "deposit".
- Lowercase, no emojis, no explanations. If you can't tell what the product is, translate
  its words into English as well as you can."""

RECEIPT_PROMPT = f"""You read photos of shop receipts for an expense tracker.

Most receipts are Finnish. List every purchased item on the receipt:
- name: the product's short shopping-list name in English. Naming rules:
{NAMING_RULES}
- price: the final amount paid for that line as a number, after quantity
  (e.g. "2 x 1,29" -> 2.58). Decimals are often written with a comma: "2,32" means 2.32.

Special lines:
- Discounts (ALENNUS, "-0,50", etc.) belong to the product right above them: subtract the
  discount from that product's price and don't list the discount on its own.
- Bottle/can deposit (PANTTI) is money paid: list it as its own item named "deposit".
- Skip lines that are not products: subtotal, total (YHTEENSÄ), VAT (ALV), payment method
  (KORTTI, PANKKIKORTTI, KÄTEINEN), change (VAIHTORAHA), loyalty bonus/points (BONUS, PLUSSA).

If the image is not a receipt or nothing is readable, return an empty list."""

ENGLISH_PROMPT = f"""You name products for a shopping expense tracker. The names were typed
by users in any language (mostly Finnish or English) and are often too detailed.

Give each name's short shopping-list name in English. Rules:
{NAMING_RULES}

Return one item per name, with name copied exactly as given."""


class ReceiptItem(BaseModel):
    name: str
    price: float


class Receipt(BaseModel):
    items: list[ReceiptItem]


class EnglishName(BaseModel):
    name: str
    english: str


class EnglishNames(BaseModel):
    items: list[EnglishName]


def clean(name):
    return name.strip().lower()


async def read_receipt(image: bytes):
    """Ask Claude for the products on a receipt photo.

    Returns [{"product_name", "price"}] with the names in English.
    """
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
        {"product_name": clean(i.name), "price": i.price}
        for i in response.parsed_output.items
    ]


async def english_names(names):
    """Ask Claude for the short English names of products typed in any language.

    Returns {name: english name}; names Claude skipped are left out.
    """
    response = await client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=ENGLISH_PROMPT,
        messages=[{"role": "user", "content": json.dumps(names, ensure_ascii=False)}],
        output_format=EnglishNames,
    )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        return {}
    wanted = set(names)
    return {
        i.name: clean(i.english)
        for i in response.parsed_output.items
        if i.name in wanted
    }
