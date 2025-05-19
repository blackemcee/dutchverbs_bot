import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# Загрузка словаря глаголов
with open("verbs_with_conjugations_and_translations.json", encoding="utf-8") as f:
    VERBS = json.load(f)

# Формирование ответа
def format_verb_output(infinitive: str, data: dict) -> str:
    tt = data.get("tegenwoordige_tijd", {})
    vt = data.get("verleden_tijd", {})
    vd = data.get("voltooid_deelwoord", "")
    hw = data.get("hulpwerkwoord", "")
    eng = data.get("english", "")

    if isinstance(hw, list):
        hw_str = " / ".join(hw)
    else:
        hw_str = hw

    response = f"📖 *{infinitive}* — {eng or 'no translation'}\n"
    response += f"\n*Infinitief:* {infinitive}"
    response += f"\n*Tegenwoordige tijd:* ik {tt.get('ik')}, jij {tt.get('jij')}, hij {tt.get('hij')}\n"
    response += f"  wij {tt.get('wij')}, jullie {tt.get('jullie')}, zij {tt.get('zij')}"
    response += f"\n*Verleden tijd:* ik {vt.get('ik')}, wij {vt.get('wij')}"
    response += f"\n*Voltooid deelwoord:* {hw_str} {vd}" if vd else ""
    return response

# Поиск по инфинитиву или частичному совпадению
def search_verbs(query: str):
    query = query.lower().strip()
    if query in VERBS:
        return [(query, VERBS[query])], True

    results = []
    for infinitive, data in VERBS.items():
        if query in infinitive:
            results.append((infinitive, data))
    return results, False

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправь мне голландский глагол, и я покажу его спряжения и перевод."
    )

# Обработка текстового сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    matches, exact = search_verbs(query)

    if not matches:
        await update.message.reply_text("Извини, я не знаю такого глагола.")
        return

    if exact:
        infinitive, data = matches[0]
        response = format_verb_output(infinitive, data)
        await update.message.reply_markdown(response)
    else:
        keyboard = [
            [InlineKeyboardButton(word, callback_data=f"verb:{word}")]
            for word, _ in matches[:20]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Выбери нужный глагол:", reply_markup=reply_markup
        )

# Обработка нажатия кнопки
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("verb:"):
        infinitive = query.data[5:]
        data = VERBS.get(infinitive)
        if data:
            response = format_verb_output(infinitive, data)
            await query.edit_message_text(response, parse_mode="Markdown")

# Запуск бота
app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_button))

if __name__ == '__main__':
    app.run_polling()