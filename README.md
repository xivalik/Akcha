# Akcha

A Telegram bot for tracking grocery expenses. Type a product and its price, or send a photo of a receipt, and Claude turns it into a short English list of what you spent.

## Features

- **Type a purchase**: `maito 2,5` is saved as `milk — 2.5 €`
- **Send a receipt photo**: every item on it is read and saved (works with Finnish receipts)
- **`/expenses`**: totals per product, most expensive first
- **Undo**: each saved item has an Undo button

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
BOT_TOKEN=your-telegram-bot-token
CLAUDE_API_KEY=your-anthropic-api-key
```

Run:

```bash
python bot.py
```

Data is stored in SQLite at `data/bot.db`, or in the Railway volume when deployed there.
