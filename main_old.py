import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

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

        if any(query in form for form in forms if form):
            return infinitive, data
    return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stuur me een Nederlands werkwoord — ik geef je alle vormen en vertaling.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verb = update.message.text
    infinitive, data = find_verb(verb)

    if not data:
        await update.message.reply_text("Sorry, ik ken dit werkwoord niet. Probeer een ander.")
        return

    tt = data.get("tegenwoordige_tijd", {})
    vt = data.get("verleden_tijd", {})

    response = f"\U0001F4D6 *{infinitive}* — {data.get('russisch', 'перевод неизвестен')}\n"
    response += f"\n*Infinitief:* {infinitive}"
    response += f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
    response += f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
    response += f"\n*Voltooid deelwoord:* {data.get('voltooid_deelwoord')}"
    response += f"\n*Hulpwerkwoord:* {data.get('hulpwerkwoord')}"

    await update.message.reply_markdown(response)

app = ApplicationBuilder().token("8063866034:AAEp0_cYkvV0raFBBmyfGCkx_1ONyL5xlfw").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    app.run_polling()
