from datetime import datetime
from functools import wraps
from io import BytesIO

from fpdf import FPDF
from fpdf.fonts import FontFace
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import ADMIN_ID
from db.database import get_all_tables



def admin_only(func):
    """Silently ignore everyone except the admin."""

    @wraps(func)
    async def wrapper(update, context):
        if update.effective_user.id != ADMIN_ID:
            return
        return await func(update, context)

    return wrapper


@admin_only
async def admin_panel(update, context):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📄 Database PDF", callback_data="admin:db")]]
    )
    await update.effective_message.reply_text(
        "Admin panel 🛠\n\n/db - the entire database as a PDF", reply_markup=keyboard
    )


@admin_only
async def send_db(update, context):
    if update.callback_query:
        await update.callback_query.answer()
    now = datetime.now()
    await update.effective_message.reply_document(
        build_db_pdf(now), filename=f"db_{now:%Y-%m-%d_%H-%M}.pdf"
    )


def build_db_pdf(now):
    """Draw every table of the database into a PDF and return it in memory."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(text=f"Database export {now:%Y-%m-%d %H:%M}", new_x="LMARGIN", new_y="NEXT")

    for name, (columns, rows) in get_all_tables().items():
        pdf.ln(6)
        pdf.set_font("Helvetica", size=13)
        pdf.cell(text=f"{name} ({len(rows)} rows)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", size=9)
        heading = FontFace(emphasis="", fill_color=(225, 225, 225))
        with pdf.table(headings_style=heading) as table:
            table.row(columns)
            for row in rows:
                table.row(["" if v is None else to_latin(str(v)) for v in row])

    return BytesIO(pdf.output())


def to_latin(text):
    """The built-in PDF font only knows Latin letters; old non-English names become '?'."""
    return text.encode("latin-1", "replace").decode("latin-1")
