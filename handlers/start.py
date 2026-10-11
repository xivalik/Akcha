from db.database import save_user
from handlers.texts import t, user_lang


async def start(update, context):
    user = update.effective_user
    save_user(user.id)
    await update.effective_message.reply_text(t(user_lang(user), "hi", name=user.first_name))
