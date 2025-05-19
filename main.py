import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load verbs from JSON
def load_verbs():
    with open("verbs.json", encoding="utf-8") as f:
        return json.load(f)

VERBS = load_verbs()
MAX_VERBS_PER_PAGE = 10

# Normalize and find verbs that match
def search_verbs(query):
    query = query.lower().strip()
    matches = []
    for infinitive, data in VERBS.items():
        forms = [infinitive]
        forms += list(data.get("tegenwoordige_tijd", {}).values())
        forms += list(data.get("verleden_tijd", {}).values())
        forms.append(data.get("voltooid_deelwoord", ""))
        if any(query in form for form in forms if form):
            matches.append(infinitive)
    return matches

# Format full verb info
def format_verb_output(infinitive, data):
    tt = data.get("tegenwoordige_tijd", {})
    vt = data.get("verleden_tijd", {})
    vd = data.get("voltooid_deelwoord", "")
    hulp = data.get("hulpwerkwoord", "")
    eng = data.get("english", "")

    output = f"📖 *{infinitive}* — {eng or 'no translation'}\n"
    output += f"\n*Infinitief:* {infinitive}"
    output += (
        f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n"
        f"  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
    )
    output += f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
    if hulp and vd:
        output += f"\n*Voltooid deelwoord:* {hulp} {vd}"
    elif vd:
        output += f"\n*Voltooid deelwoord:* {vd}"
    else:
        output += "\n*Voltooid deelwoord:* -"
    return output

# Telegram Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Stuur me een Nederlands werkwoord of een vervoegde vorm — ik geef je alle vormen en Engelse vertaling."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    matches = search_verbs(query)

    if not matches:
        await update.message.reply_text("Geen werkwoord gevonden. Probeer een andere vorm.")
        return

    if len(matches) == 1:
        infinitive = matches[0]
        data = VERBS.get(infinitive, {})
        response = format_verb_output(infinitive, data)
        await update.message.reply_markdown(response)
    else:
        context.user_data["matches"] = matches
        context.user_data["page"] = 0
        await send_verb_selection(update, context)

def get_page(matches, page, per_page=MAX_VERBS_PER_PAGE):
    start = page * per_page
    end = start + per_page
    return matches[start:end]

async def send_verb_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = context.user_data.get("matches", [])
    page = context.user_data.get("page", 0)

    keyboard = []
    for infinitive in get_page(matches, page):
        keyboard.append([InlineKeyboardButton(infinitive, callback_data=f"verb:{infinitive}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Vorige", callback_data="nav:prev"))
    if (page + 1) * MAX_VERBS_PER_PAGE < len(matches):
        nav_buttons.append(InlineKeyboardButton("Volgende ➡️", callback_data="nav:next"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Meerdere werkwoorden gevonden. Kies:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("verb:"):
        infinitive = query.data.split("verb:")[1]
        data = VERBS.get(infinitive, {})
        response = format_verb_output(infinitive, data)
        await query.edit_message_text(response, parse_mode="Markdown")
    elif query.data == "nav:next":
        context.user_data["page"] += 1
        await query.message.delete()
        await send_verb_selection(update, context)
    elif query.data == "nav:prev":
        context.user_data["page"] -= 1
        await query.message.delete()
        await send_verb_selection(update, context)

# App initialization
app = ApplicationBuilder().token("8063866034:AAEp0_cYkvV0raFBBmyfGCkx_1ONyL5xlfw").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback))

if __name__ == '__main__':
    app.run_polling()
