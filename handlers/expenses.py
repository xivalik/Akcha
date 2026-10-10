from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db.database import add_products, delete_products, get_currency, get_products

# Phone keyboards auto-replace ' " - with curly/long versions; turn them back
SMART_PUNCTUATION = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})
# Longest product name shown in /expenses before it gets cut with "…"
MAX_NAME_WIDTH = 18


def format_price(price):
    """Round to cents and drop a useless .0: 3.0 -> 3, 3.5 -> 3.5, 0.1 + 0.2 -> 0.3."""
    price = round(price, 2)
    return int(price) if float(price).is_integer() else price


async def expenses(update, context):
    user = update.effective_user
    rows = get_products(user.id)
    if not rows:
        await update.effective_message.reply_text("You have no products yet.")
        return
    sign = get_currency(user.id)
    # Cut long names so the table doesn't wrap on narrow phone screens
    names = [n if len(n) <= MAX_NAME_WIDTH else n[:MAX_NAME_WIDTH - 1] + "…"
             for n in (r["product_name"] for r in rows)]
    prices = [f"{sign}{format_price(r['price'])}" for r in rows]
    total = f"{sign}{format_price(sum(r['price'] for r in rows))}"

    name_width = max(len(n) for n in names + ["Total"])
    price_width = max(len(p) for p in prices + [total])
    lines = [f"{n.ljust(name_width)}  {p.rjust(price_width)}" for n, p in zip(names, prices)]
    lines.append("─" * (name_width + 2 + price_width))
    lines.append(f"{'Total'.ljust(name_width)}  {total.rjust(price_width)}")
    # Pad first, then escape() — escaping "&" to "&amp;" would throw off the column widths
    table = escape("\n".join(lines))
    await update.effective_message.reply_text(f"<pre>{table}</pre>", parse_mode="HTML")


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
    added = f"{item['product_name']}: {get_currency(user.id)}{format_price(item['price'])}"
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
