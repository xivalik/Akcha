TEXTS = {
    "hi": "Hi {name}👋",
    "no_products": "You have no products yet.",
    "total": "Total",
    "format_help": "Please use the format: product price\nFor example: apple 3",
    "bad_name": "Please write the product name with letters, digits and symbols only (no emojis).",
    "added": "Added ✅\n",
    "confirm_undo": "\n\nDo you really want to cancel this record?",
    "undo": "↩️ Undo",
    "yes": "✅ Yes",
    "no": "❌ No",
    "kept": "Kept.",
    "removed": "Removed.",
    "already_removed": "Already removed.",
    "cancelled": "Cancelled ❌\n",
    "receipt_failed": "Sorry, I couldn't read the receipt right now. Please try again later.",
    "receipt_empty": "I couldn't find any products on this photo. Try a clearer photo of the receipt.",
    "name_failed": "Sorry, I couldn't add the product right now. Please try again later.",
    "reading_receipt": "Reading your receipt",
    "adding_product": "Adding your product",
}


def t(key, **kwargs):
    """The text for key, with {placeholders} filled in."""
    return TEXTS[key].format(**kwargs)
