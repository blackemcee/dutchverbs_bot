import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

def load_verbs():
    with open("verbs.json", encoding="utf-8") as f:
        return json.load(f)

VERBS = load_verbs()

def find_matching_verbs(query):
    query = query.lower().strip()
    matches = []
    for infinitive, data in VERBS.items():
        forms = [infinitive]
        forms += list(data.get("tegenwoordige_tijd", {}).values())
        forms += list(data.get("verleden_tijd", {}).values())
        forms.append(data.get("voltooid_deelwoord", ""))
        if any(query == form for form in forms if form):
            return [infinitive]
        if any(query in form for form in forms if form):
            matches.append(infinitive)
    return matches

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Stuur me een Nederlands werkwoord — ik geef je alle vormen en vertaling."
    )

async def send_verb_info(target, data, infinitive):
    tt = data.get("tegenwoordige_tijd", {})
    vt = data.get("verleden_tijd", {})
    response = f"\U0001F4D6 *{infinitive}* — {data.get('russisch', 'перевод неизвестен')}\n"
    response += f"\n*Infinitief:* {infinitive}"
    response += f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
    response += f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
    response += f"\n*Voltooid deelwoord:* {data.get('voltooid_deelwoord')}"
    response += f"\n*Hulpwerkwoord:* {data.get('hulpwerkwoord')}"
    await target.edit_message_text(response, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    matches = find_matching_verbs(query)

    if not matches:
        await update.message.reply_text("Sorry, ik ken dit werkwoord niet. Probeer een ander.")
        return

    if len(matches) == 1:
        infinitive = matches[0]
        data = VERBS[infinitive]
        await update.message.reply_markdown(
            f"\U0001F4D6 *{infinitive}* — {data.get('russisch', 'перевод неизвестен')}\n"
            f"\n*Infinitief:* {infinitive}"
            f"\n*Tegenwoordige tijd:* ik {data['tegenwoordige_tijd']['ik']}, jij {data['tegenwoordige_tijd']['jij']}, hij {data['tegenwoordige_tijd']['hij']}\n"
            f"  wij {data['tegenwoordige_tijd']['wij']}, jullie {data['tegenwoordige_tijd']['jullie']}, zij {data['tegenwoordige_tijd']['zij']}"
            f"\n*Verleden tijd:* ik {data['verleden_tijd']['ik']}, wij {data['verleden_tijd']['wij']}"
            f"\n*Voltooid deelwoord:* {data['voltooid_deelwoord']}"
            f"\n*Hulpwerkwoord:* {data['hulpwerkwoord']}"
        )
        return

    # Multiple matches: show options as buttons
    keyboard = [
        [InlineKeyboardButton(verb, callback_data=verb[:64])] for verb in matches[:10]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Meerdere werkwoorden gevonden. Kies één:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    verb = query.data
    data = VERBS.get(verb)
    if data:
        tt = data.get("tegenwoordige_tijd", {})
        vt = data.get("verleden_tijd", {})
        response = f"\U0001F4D6 *{verb}* — {data.get('russisch', 'перевод неизвестен')}\n"
        response += f"\n*Infinitief:* {verb}"
        response += f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
        response += f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
        response += f"\n*Voltooid deelwoord:* {data.get('voltooid_deelwoord')}"
        response += f"\n*Hulpwerkwoord:* {data.get('hulpwerkwoord')}"
        await query.edit_message_text(response, parse_mode="Markdown")
    else:
        await query.edit_message_text("Dit werkwoord bestaat niet (meer).")

def main():
    app = ApplicationBuilder().token("8063866034:AAEp0_cYkvV0raFBBmyfGCkx_1ONyL5xlfw").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running!")
    app.run_polling()

if __name__ == '__main__':
    main()