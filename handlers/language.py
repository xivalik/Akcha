from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db.database import set_language
from handlers.texts import LANGUAGES, t, user_lang


async def language(update, context):
    lang = user_lang(update.effective_user)
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(name, callback_data=f"language:{code}")
                for code, name in LANGUAGES.items()
            ]
        ]
    )
    await update.effective_message.reply_text(
        t(lang, "choose_language"), reply_markup=keyboard
    )


async def choose_language(update, context):
    query = update.callback_query
    code = query.data.split(":", 1)[1]
    if code not in LANGUAGES:
        await query.answer()
        return
    set_language(update.effective_user.id, code)
    await query.answer(t(code, "saved"))
    await query.edit_message_text(t(code, "language_set"))
