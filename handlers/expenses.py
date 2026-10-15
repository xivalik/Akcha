import logging
import unicodedata
from html import escape

import anthropic
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from claude import english_names
from db.database import add_products, delete_products, get_products
from handlers.loading import loading
from handlers.texts import t

logger = logging.getLogger(__name__)

# Phone keyboards auto-replace ' " - with curly/long versions; turn them back
SMART_PUNCTUATION = str.maketrans(
    {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"}
)


def is_valid_name(name):
    """Letters of any language (ä, ö, å...), digits and keyboard symbols; no emojis.

    isprintable() rejects invisible/control characters, and emojis are "So" (other symbol).
    """
    return bool(name) and name.isprintable() and not any(
        unicodedata.category(c) == "So" for c in name
    )


def format_price(price):
    """Round to cents and drop a useless .0: 3.0 -> 3, 3.5 -> 3.5, 0.1 + 0.2 -> 0.3."""
    price = round(price, 2)
    return int(price) if float(price).is_integer() else price


def format_money(price):
    """HTML for a price: the euro sign in italics."""
    return f"{format_price(price)} <i>€</i>"


async def expenses(update, context):
    msg = update.effective_message
    rows = get_products(update.effective_user.id)
    if not rows:
        await msg.reply_text(t("no_products"))
        return
    # escape() so names like "M&M" or "<3" don't break the HTML formatting
    lines = [f"{escape(r['product_name'])} — {format_money(r['price'])}" for r in rows]
    total = sum(r["price"] for r in rows)
    lines.append("──────────────")
    lines.append(f"{t('total')} — {format_money(total)}")
    text = "\n".join(lines)
    await msg.reply_text(f"<b>{text}</b>", parse_mode="HTML")


async def add_product_request(update, context):
    msg = update.effective_message
    *name, price = msg.text.translate(SMART_PUNCTUATION).split()
    try:
        # Many keyboards/locales write decimals with a comma: 2,32 -> 2.32
        price = float(price.replace(",", "."))
    except ValueError:
        name = None
    if not name:
        await msg.reply_text(t("format_help"))
        return
    name = " ".join(name)
    if not is_valid_name(name):
        await msg.reply_text(t("bad_name"))
        return

    # Products are only saved in English: "maito 2" is saved as "milk"
    try:
        async with loading(msg, t("adding_product")):
            english = (await english_names([name])).get(name)
    except anthropic.APIError:
        logger.exception("Naming a product in English failed")
        english = None
    if not english or not is_valid_name(english):
        await msg.reply_text(t("name_failed"))
        return

    item = {"product_name": english, "price": price}
    await save_and_reply(msg, update.effective_user.id, item)


def undo_keyboard(ids):
    """The Undo button for products with ids "first:last"."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("undo"), callback_data=f"undo:{ids}")]]
    )


async def save_and_reply(msg, tg_id, item):
    """Save one product and reply "Added ✅" with an Undo button for it."""
    first_id, last_id = add_products(tg_id, [item])
    added = f"{escape(item['product_name'])} — {format_money(item['price'])}"
    await msg.reply_text(
        f"{t('added')}{added}",
        parse_mode="HTML",
        reply_markup=undo_keyboard(f"{first_id}:{last_id}"),
    )


async def undo_ask(update, context):
    """Undo tapped: ask for confirmation before deleting anything."""
    query = update.callback_query
    ids = query.data.removeprefix("undo:")
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(t("yes"), callback_data=f"undo_yes:{ids}"),
            InlineKeyboardButton(t("no"), callback_data=f"undo_no:{ids}"),
        ]]
    )
    await query.answer()
    # text_html keeps the italics; plain .text would lose them
    await query.edit_message_text(
        query.message.text_html + t("confirm_undo"),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def undo_keep(update, context):
    """No: put the message back the way it was, with the Undo button."""
    query = update.callback_query
    ids = query.data.removeprefix("undo_no:")
    await query.answer(t("kept"))
    text = query.message.text_html.removesuffix(t("confirm_undo"))
    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=undo_keyboard(ids)
    )


async def undo_add(update, context):
    """Yes: delete the products and mark the message as cancelled."""
    query = update.callback_query
    _, first_id, last_id = query.data.split(":")
    deleted = delete_products(update.effective_user.id, int(first_id), int(last_id))
    items = query.message.text_html.removeprefix(t("added")).removesuffix(t("confirm_undo"))
    await query.answer(t("removed" if deleted else "already_removed"))
    await query.edit_message_text(f"{t('cancelled')}{items}", parse_mode="HTML")
