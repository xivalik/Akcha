from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db.database import get_currency, set_currency

CURRENCIES = ["$", "€", "₽", "SUM"]


async def currency(update, context):
    current = get_currency(update.effective_user.id)
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(sign, callback_data=f"currency:{sign}")
                for sign in CURRENCIES
            ]
        ]
    )
    await update.effective_message.reply_text(
        f"Choose your currency (current: <i>{current}</i>)",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def choose_currency(update, context):
    query = update.callback_query
    sign = query.data.split(":", 1)[1]
    if sign not in CURRENCIES:
        await query.answer()
        return
    set_currency(update.effective_user.id, sign)
    await query.answer("Saved.")
    await query.edit_message_text(f"Currency set to <i>{sign}</i> ✅", parse_mode="HTML")
