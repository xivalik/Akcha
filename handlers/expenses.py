import logging

import anthropic
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from claude import parse_purchases
from db.database import add_products, delete_products, get_products


async def expenses(update, context):
    user = update.effective_user
    rows = get_products(user.id)
    if not rows:
        await update.effective_message.reply_text("You have no products yet.")
        return
    lines = [f"{r['product_name']}: {r['price']}" for r in rows]
    total = sum(r["price"] for r in rows)
    lines.append(f"\nTotal: {total}")
    await update.effective_message.reply_text("\n".join(lines))


async def add_product_request(update, context):
    user = update.effective_user
    msg = update.effective_message
    try:
        items = await parse_purchases(msg.text)
    except anthropic.APIError:
        logging.exception("Claude request failed")
        await msg.reply_text(
            "Sorry, I couldn't process that right now. Try again in a moment."
        )
        return

    if not items:
        await msg.reply_text(
            "I didn't find a product and price there. Try something like: apple 3"
        )
        return

    first_id, last_id = add_products(user.id, items)
    added = "\n".join(f"{i['product_name']}: {i['price']}" for i in items)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("↩️ Undo", callback_data=f"undo:{first_id}:{last_id}")]]
    )
    await msg.reply_text(f"Added ✅\n{added}", reply_markup=keyboard)


async def undo_add(update, context):
    query = update.callback_query
    _, first_id, last_id = query.data.split(":")
    deleted = delete_products(update.effective_user.id, int(first_id), int(last_id))
    if not deleted:
        await query.answer("Already removed.")
        await query.edit_message_reply_markup(reply_markup=None)
        return
    await query.answer("Removed.")
    items = query.message.text.removeprefix("Added ✅\n")
    await query.edit_message_text(f"Cancelled ❌\n{items}")
