import logging
import unicodedata
from html import escape

import anthropic
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from claude import english_name
from db.database import delete_product, get_products, save_product

logger = logging.getLogger(__name__)

# Phone keyboards auto-replace ' " - with curly/long versions; turn them back
SMART_PUNCTUATION = str.maketrans(
    {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"}
)
# The undo handlers cut these off a message to get back the product line in it
ADDED = "Added ✅\n"
CONFIRM_UNDO = "\n\nDo you really want to cancel this record?"


def is_valid_name(name):
    """Letters of any language (ä, ö, å...), digits and keyboard symbols; no emojis.

    isprintable() rejects invisible/control characters, and emojis are "So" (other symbol).
    """
    return bool(name) and name.isprintable() and not any(
        unicodedata.category(c) == "So" for c in name
    )


def format_money(price):
    """HTML for a price, rounded to cents and with the euro sign in italics.

    A useless .0 is dropped: 3.0 -> 3, 3.5 -> 3.5, 0.1 + 0.2 -> 0.3.
    """
    price = round(price, 2)
    if float(price).is_integer():
        price = int(price)
    return f"{price} <i>€</i>"


async def expenses(update, context):
    msg = update.effective_message
    products = get_products(update.effective_user.id)
    if not products:
        await msg.reply_text("You have no products yet.")
        return
    # escape() so names like "M&M" or "<3" don't break the HTML formatting
    lines = [f"{escape(p['product_name'])} — {format_money(p['price'])}" for p in products]
    total = sum(p["price"] for p in products)
    lines.append("──────────────")
    lines.append(f"Total — {format_money(total)}")
    text = "\n".join(lines)
    await msg.reply_text(f"<b>{text}</b>", parse_mode="HTML")


async def add_product(update, context):
    """A typed message like "maito 2,5": save it as "milk — 2.5 €"."""
    msg = update.effective_message
    *words, last_word = msg.text.translate(SMART_PUNCTUATION).split()
    try:
        # Many keyboards/locales write decimals with a comma: 2,32 -> 2.32
        price = float(last_word.replace(",", "."))
    except ValueError:
        price = None
    if not words or price is None:
        await msg.reply_text("Please use the format: product price\nFor example: apple 3")
        return
    name = " ".join(words)
    if not is_valid_name(name):
        await msg.reply_text(
            "Please write the product name with letters, digits and symbols only (no emojis)."
        )
        return

    # Products are only saved in English: "maito 2" is saved as "milk"
    try:
        english = await english_name(name)
    except anthropic.APIError:
        logger.exception("Naming a product in English failed")
        english = None
    if not english or not is_valid_name(english):
        await msg.reply_text(
            "Sorry, I couldn't add the product right now. Please try again later."
        )
        return

    await save_and_reply(msg, update.effective_user.id, english, price)


def undo_keyboard(product_id):
    """The Undo button under an "Added ✅" message."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("↩️ Undo", callback_data=f"undo:{product_id}")]]
    )


async def save_and_reply(msg, tg_id, name, price):
    """Save one product and reply "Added ✅" with an Undo button for it."""
    product_id = save_product(tg_id, name, price)
    await msg.reply_text(
        f"{ADDED}{escape(name)} — {format_money(price)}",
        parse_mode="HTML",
        reply_markup=undo_keyboard(product_id),
    )


async def undo_ask(update, context):
    """Undo tapped: ask for confirmation before deleting anything."""
    query = update.callback_query
    product_id = query.data.removeprefix("undo:")
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Yes", callback_data=f"undo_yes:{product_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"undo_no:{product_id}"),
        ]]
    )
    await query.answer()
    # text_html keeps the italics; plain .text would lose them
    await query.edit_message_text(
        query.message.text_html + CONFIRM_UNDO,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def undo_no(update, context):
    """No: put the message back the way it was, with the Undo button."""
    query = update.callback_query
    product_id = query.data.removeprefix("undo_no:")
    await query.answer("Kept.")
    text = query.message.text_html.removesuffix(CONFIRM_UNDO)
    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=undo_keyboard(product_id)
    )


async def undo_yes(update, context):
    """Yes: delete the product and mark the message as cancelled."""
    query = update.callback_query
    product_id = int(query.data.removeprefix("undo_yes:"))
    deleted = delete_product(update.effective_user.id, product_id)
    product_line = query.message.text_html.removeprefix(ADDED).removesuffix(CONFIRM_UNDO)
    await query.answer("Removed." if deleted else "Already removed.")
    await query.edit_message_text(f"Cancelled ❌\n{product_line}", parse_mode="HTML")
