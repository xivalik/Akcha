import base64
import json

import anthropic
from pydantic import BaseModel

from config import CLAUDE_API

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API)
MODEL = "claude-haiku-5-5"

LANGUAGE_NAMES = {"en": "English", "fi": "Finnish"}

TRANSLATION_RULES = """- Use the short everyday name a shopper would say ("ruisleipä" -> "rye bread").
- Keep brand names as they are; translate only the generic words ("valio maito" -> "valio milk").
- Lowercase, no emojis, no explanations. If a name is already in the target language, keep it."""

RECEIPT_PROMPT = f"""You read photos of shop receipts for an expense tracker.

Most receipts are Finnish. List every purchased item on the receipt:
- name: the product name in the receipt's own language (do not translate), lowercase, keeping
  letters like ä, ö, å. Write cut-off words in full when it's obvious ("ruisleip" -> "ruisleipä").
  No emojis.
- en, fi: the same product name in English and in Finnish (one of them is usually the same
  as name). Translation rules:
{TRANSLATION_RULES}
- price: the final amount paid for that line as a number, after quantity
  (e.g. "2 x 1,29" -> 2.58). Decimals are often written with a comma: "2,32" means 2.32.

Special lines:
- Discounts (ALENNUS, "-0,50", etc.) belong to the product right above them: subtract the
  discount from that product's price and don't list the discount on its own.
- Bottle/can deposit (PANTTI) is money paid: list it as its own item named "pantti".
- Skip lines that are not products: subtotal, total (YHTEENSÄ), VAT (ALV), payment method
  (KORTTI, PANKKIKORTTI, KÄTEINEN), change (VAIHTORAHA), loyalty bonus/points (BONUS, PLUSSA).

If the image is not a receipt or nothing is readable, return an empty list."""

TRANSLATE_PROMPT = f"""You translate product names for a shopping expense tracker. The names
were typed by users or read from receipts, mostly in Finnish or English.

Translate each name into the language you are asked for. Rules:
{TRANSLATION_RULES}

Return one item per name, with name copied exactly as given."""


class ReceiptItem(BaseModel):
    name: str
    en: str
    fi: str
    price: float


class Receipt(BaseModel):
    items: list[ReceiptItem]


class Translation(BaseModel):
    name: str
    translation: str


class Translations(BaseModel):
    items: list[Translation]


def clean(name):
    return name.strip().lower()


async def read_receipt(image: bytes):
    """Ask Claude for the products on a receipt photo.

    Returns [{"product_name", "price", "translations": {"en": ..., "fi": ...}}].
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
        {
            "product_name": clean(i.name),
            "price": i.price,
            "translations": {"en": clean(i.en), "fi": clean(i.fi)},
        }
        for i in response.parsed_output.items
    ]


async def translate_names(names, language):
    """Ask Claude to translate product names into language ("en"/"fi").

    Returns {name: translation}; names Claude skipped are left out.
    """
    response = await client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=TRANSLATE_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Translate into {LANGUAGE_NAMES[language]}:\n"
                + json.dumps(names, ensure_ascii=False),
            }
        ],
        output_format=Translations,
    )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        return {}
    wanted = set(names)
    return {
        i.name: clean(i.translation)
        for i in response.parsed_output.items
        if i.name in wanted
    }
