from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db.database import add_products, delete_products, get_products

# Phone keyboards auto-replace ' " - with curly/long versions; turn them back
SMART_PUNCTUATION = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


async def expenses(update, context):
    user = update.effective_user
    rows = get_products(user.id)
    if not rows:
        await update.effective_message.reply_text("You have no products yet.")
        return
    # escape() so names like "M&M" or "<3" don't break the HTML formatting
    lines = [f"<b>{escape(r['product_name'])}</b>: {r['price']}" for r in rows]
    total = sum(r["price"] for r in rows)
    lines.append(f"\n<b>Total:</b> {total}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


async def add_product_request(update, context):
    user = update.effective_user
    msg = update.effective_message
    *name, price = msg.text.translate(SMART_PUNCTUATION).split()
    try:
        price = float(price)
    except ValueError:
        name = None
    if not name:
        await msg.reply_text("Please use the format: product price\nFor example: apple 3")
        return
    # English letters, digits and keyboard symbols (- ' & . etc.)
    if not all(word.isascii() and word.isprintable() for word in name):
        await msg.reply_text(
            "Please write the product name in English letters, digits and symbols only."
        )
        return

    item = {"product_name": " ".join(name).lower(), "price": price}
    first_id, last_id = add_products(user.id, [item])
    added = f"{item['product_name']}: {item['price']}"
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
