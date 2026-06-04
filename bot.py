import logging
import requests
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURACION
# =========================
# En Railway es mejor usar Variables de Entorno, pero dejo los strings por ahora
BOT_TOKEN = os.getenv("BOT_TOKEN", "8723973833:AAFmyX4SK3DTE15fFUKu5AiofRS3QaQ2AA4")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "goldapi-4ggdsmjfphsjl-io")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

GOLD_TYPES = {
    "10K": 10 / 24,
    "14K": 14 / 24,
    "18K": 18 / 24,
    "22K": 22 / 24,
    "24K": 1.0,
}

# =========================
# OBTENER PRECIO
# =========================
def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return float(response.json()["price"])
    except Exception as e:
        logging.error(f"Error API: {e}")
    return None

# =========================
# MENÚS
# =========================
async def main_menu(update: Update):
    keyboard = [["🥇 Calcular Precio", "📈 Precio Actual"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    text = "💸 *JCS Gold Calculator*\n\nSeleccione una opción:"
    await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode="Markdown")

async def purity_menu(update: Update):
    keyboard = [["10K", "14K"], ["18K", "22K"], ["24K"], ["⬅️ Volver"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Seleccione la pureza:", reply_markup=reply_markup)

# =========================
# HANDLERS
# =========================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    user_data = context.user_data

    if text == "📈 Precio Actual":
        price = get_gold_price_ounce()
        if price:
            await update.message.reply_text(f"📈 *Precio actual:*\n\n${price:,.2f} USD / oz", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Error al obtener precio.")

    elif text == "🥇 Calcular Precio":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    elif text == "⬅️ Volver":
        user_data.clear()
        await main_menu(update)

    elif text in GOLD_TYPES and user_data.get("step") == "select_purity":
        user_data["gold_type"] = text
        user_data["step"] = "input_grams"
        await update.message.reply_text(f"✅ {text} seleccionado. Escriba los gramos:")

    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.'))
            gold_type = user_data["gold_type"]
            price = get_gold_price_ounce()
            if price:
                total = grams * ((price / 31.1035) * GOLD_TYPES[gold_type])
                await update.message.reply_text(f"🥇 *Resultado*\n\n{grams}g de {gold_type}: *${total:,.2f} USD*", parse_mode="Markdown")
                user_data.clear()
                await main_menu(update)
        except ValueError:
            await update.message.reply_text("❌ Use solo números.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
