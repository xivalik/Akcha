import logging

import anthropic
from db.database import add_product, get_products
from claude import parse_purchases


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

    for item in items:
        add_product(user.id, item["product_name"], item["price"])
    added = "\n".join(f"{i['product_name']}: {i['price']}" for i in items)
    await msg.reply_text(f"Added ✅\n{added}")
