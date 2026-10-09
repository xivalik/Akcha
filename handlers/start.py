from db.database import save_user


async def start(update, context):
    user = update.effective_user
    save_user(user.id)
    await update.effective_message.reply_text(f"Hi {user.first_name}👋")
