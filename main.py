import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- Load verbs
def load_verbs():
    with open("verbs.json", encoding="utf-8") as f:
        return json.load(f)

VERBS = load_verbs()
VERBS_LIST = list(VERBS.keys())
PAGE_SIZE = 10

def find_verb(query):
    query = query.lower().strip()
    matches = []
    for infinitive, data in VERBS.items():
        forms = [infinitive]
        forms += list(data.get("tegenwoordige_tijd", {}).values())
        forms += list(data.get("verleden_tijd", {}).values())
        forms.append(data.get("voltooid_deelwoord", ""))
        if any(query == form for form in forms if form):
            # Exact match
            return [(infinitive, data)]
        if any(query in form for form in forms if form):
            matches.append((infinitive, data))
    return matches

def build_verb_keyboard(matches, page=0):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_matches = matches[start:end]
    keyboard = [
        [InlineKeyboardButton(text=inf, callback_data=f"showverb:{inf}")]
        for inf, _ in page_matches
    ]
    # Add pagination controls
    controls = []
    if start > 0:
        controls.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{page-1}"))
    if end < len(matches):
        controls.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))
    if controls:
        keyboard.append(controls)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stuur me een Nederlands werkwoord — ik geef je alle vormen en vertaling.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verb = update.message.text
    matches = find_verb(verb)

    if not matches:
        await update.message.reply_text("Sorry, ik ken dit werkwoord niet. Probeer een ander.")
        return

    if len(matches) == 1:
        infinitive, data = matches[0]
        await send_verb_info(update, infinitive, data)
    else:
        # Multiple matches, show paginated list
        keyboard = build_verb_keyboard(matches, page=0)
        await update.message.reply_text(
            f"Meerdere werkwoorden gevonden, kies een van de lijst:",
            reply_markup=keyboard
        )
        # Store matches in user_data for paging
        context.user_data["matches"] = matches

async def send_verb_info(update_or_query, infinitive, data, edit=False):
    tt = data.get("tegenwoordige_tijd", {})
    vt = data.get("verleden_tijd", {})
    response = (
        f"\U0001F4D6 *{infinitive}* — "
        f"{data.get('english', 'translation unknown')}\n"
        f"\n*Infinitief:* {infinitive}"
        f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n"
        f"  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
        f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
        f"\n*Voltooid deelwoord:* {data.get('voltooid_deelwoord')}"
        f"\n*Hulpwerkwoord:* {data.get('hulpwerkwoord')}"
    )
    if hasattr(update_or_query, "edit_message_text") and edit:
        await update_or_query.edit_message_text(
            response, parse_mode="Markdown"
        )
    else:
        await update_or_query.message.reply_markdown(response)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("showverb:"):
        infinitive = data.split(":", 1)[1]
        verb_data = VERBS.get(infinitive)
        if verb_data:
            await send_verb_info(query, infinitive, verb_data, edit=True)
    elif data.startswith("page:"):
        page = int(data.split(":", 1)[1])
        matches = context.user_data.get("matches", [])
        keyboard = build_verb_keyboard(matches, page)
        await query.edit_message_text(
            "Meerdere werkwoorden gevonden, kies een van de lijst:",
            reply_markup=keyboard
        )

app = ApplicationBuilder().token("8063866034:AAEp0_cYkvV0raFBBmyfGCkx_1ONyL5xlfw").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback_query))

if __name__ == '__main__':
    app.run_polling()