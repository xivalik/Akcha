from db.database import get_language

LANGUAGES = {"en": "🇬🇧 English", "fi": "🇫🇮 Suomi"}

TEXTS = {
    "en": {
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
        "choose_language": "Choose your language",
        "saved": "Saved.",
        "language_set": "Language set to English ✅",
        "reading_receipt": "Reading your receipt",
        "preparing_expenses": "Sorting your products",
    },
    "fi": {
        "hi": "Hei {name}👋",
        "no_products": "Sinulla ei ole vielä tuotteita.",
        "total": "Yhteensä",
        "format_help": "Käytä muotoa: tuote hinta\nEsimerkiksi: omena 3",
        "bad_name": "Kirjoita tuotteen nimi vain kirjaimilla, numeroilla ja merkeillä (ei emojeja).",
        "added": "Lisätty ✅\n",
        "confirm_undo": "\n\nHaluatko varmasti perua tämän merkinnän?",
        "undo": "↩️ Peru",
        "yes": "✅ Kyllä",
        "no": "❌ Ei",
        "kept": "Säilytetty.",
        "removed": "Poistettu.",
        "already_removed": "Jo poistettu.",
        "cancelled": "Peruttu ❌\n",
        "receipt_failed": "Valitettavasti en pystynyt lukemaan kuittia juuri nyt. Yritä myöhemmin uudelleen.",
        "receipt_empty": "En löytänyt kuvasta tuotteita. Kokeile selkeämpää kuvaa kuitista.",
        "choose_language": "Valitse kieli",
        "saved": "Tallennettu.",
        "language_set": "Kieleksi on valittu suomi ✅",
        "reading_receipt": "Luen kuittia",
        "preparing_expenses": "Järjestelen tuotteita",
    },
}


def user_lang(user):
    """The language the user picked, or a guess from their Telegram app language."""
    lang = get_language(user.id)
    if lang in TEXTS:
        return lang
    return "fi" if (user.language_code or "").startswith("fi") else "en"


def t(lang, key, **kwargs):
    """The text for key in the given language, with {placeholders} filled in."""
    return TEXTS[lang][key].format(**kwargs)


def strip_any(text, key, prefix=False):
    """Remove the key's text in any language from the start (prefix) or end of text.

    Messages can outlive a language switch, so the old wording must still be recognized.
    """
    for texts in TEXTS.values():
        stripped = text.removeprefix(texts[key]) if prefix else text.removesuffix(texts[key])
        if stripped != text:
            return stripped
    return text
