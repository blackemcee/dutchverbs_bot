import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

# Загрузка словаря глаголов
def load_verbs():
    with open("verbs.json", encoding="utf-8") as f:
        return json.load(f)

VERBS = load_verbs()

# Нормализация: ищем инфинитив по любой форме
def find_verb(query):
    query = query.lower().strip()
    for infinitive, data in VERBS.items():
        forms = [infinitive]
        forms += list(data.get("tegenwoordige_tijd", {}).values())
        forms += list(data.get("verleden_tijd", {}).values())
        forms.append(data.get("voltooid_deelwoord", ""))

        if any(query == form for form in forms if form):
            return infinitive, data
    # Если не точное совпадение — ищем как часть слова
    matches = []
    for infinitive, data in VERBS.items():
        forms = [infinitive]
        forms += list(data.get("tegenwoordige_tijd", {}).values())
        forms += list(data.get("verleden_tijd", {}).values())
        forms.append(data.get("voltooid_deelwoord", ""))
        if any(query in form for form in forms if form):
            matches.append(infinitive)
    return None, matches if matches else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stuur me een Nederlands werkwoord — ik geef je alle vormen en vertaling.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    infinitive, data_or_matches = find_verb(query)

    if not data_or_matches:
        await update.message.reply_text("Sorry, ik ken dit werkwoord niet. Probeer een ander.")
        return

    if infinitive:
        await send_verb_info(update, infinitive, data_or_matches)
    else:
        buttons = [
            [InlineKeyboardButton(text=verb, callback_data=verb)]
            for verb in sorted(data_or_matches)[:20]  # максимум 20 кнопок
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Welke bedoel je?", reply_markup=reply_markup)

async def send_verb_info(update_or_callback, infinitive, data):
    tt = data.get("tegenwoordige_tijd", {})
    vt = data.get("verleden_tijd", {})
    vd = data.get("voltooid_deelwoord", "")
    hulp = data.get("hulpwerkwoord", "").strip()
    translation = data.get("english", "translation unknown")

    if hulp:
        voltooid_str = f"{hulp} {vd}" if "/" not in hulp else f"{' / '.join(hulp.split('/'))} {vd}"
    else:
        voltooid_str = vd or "-"

    response = f"📖 *{infinitive}* — {translation}\n"
    response += f"\n*Infinitief:* {infinitive}"
    response += f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n" \
                f"  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
    response += f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
    response += f"\n*Voltooid deelwoord:* {voltooid_str}"

    await update_or_callback.message.reply_markdown(response)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    infinitive = query.data
    data = VERBS.get(infinitive)
    if data:
        await send_verb_info(query, infinitive, data)
    else:
        await query.message.reply_text("Er is een fout opgetreden.")

# --- Запуск приложения ---
app = ApplicationBuilder().token("8063866034:AAEp0_cYkvV0raFBBmyfGCkx_1ONyL5xlfw").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_button))

if __name__ == '__main__':
    app.run_polling()
