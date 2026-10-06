import random
from claude import ask_claude

async def roll(update, context):
    sides = 6
    if context.args:
        try:
            sides = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Please enter integer after /roll command")
            return
        if sides < 1:
            await update.message.reply_text("The number must be at least 1")
            return
    await update.message.reply_text(f"🎲{random.randint(1, sides)}")

async def claude(update, context):
    if context.args:
        await update.message.reply_text(await ask_claude(" ".join(context.args)))
        return
    await update.message.reply_text("write your prompt after \"/claude\" command")