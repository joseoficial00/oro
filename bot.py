import logging
import requests
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
BOT_TOKEN = "8723973833:AAFmyX4SK3DTE15fFUKu5AiofRS3QaQ2AA4"
GOLD_API_KEY = "goldapi-4ggdsmjfphsjl-io"

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
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return float(response.json()["price"])
    except:
        return None
    return None

# =========================
# MENÚS (REPLY KEYBOARD)
# =========================

async def main_menu(update: Update):
    # He quitado soporte, ahora los dos botones principales quedan en una fila
    keyboard = [
        ["🥇 Calcular Precio", "📈 Precio Actual"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = "💸 *JCS Gold Calculator*\n\nBienvenido. Seleccione una opción:"
    await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode="Markdown")

async def purity_menu(update: Update):
    keyboard = [
        ["10K", "14K"],
        ["18K", "22K"],
        ["24K"],
        ["⬅️ Volver"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Seleccione la pureza del oro:", reply_markup=reply_markup)

# =========================
# PROCESAMIENTO DE MENSAJES
# =========================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    # --- PRECIO ACTUAL ---
    if text == "📈 Precio Actual":
        price = get_gold_price_ounce()
        if price:
            await update.message.reply_text(f"📈 *Precio actual del oro:*\n\n${price:,.2f} USD por onza", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No se pudo obtener el precio en este momento.")

    # --- INICIAR CÁLCULO ---
    elif text == "🥇 Calcular Precio":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    # --- VOLVER AL INICIO ---
    elif text == "⬅️ Volver":
        user_data.clear()
        await main_menu(update)

    # --- LÓGICA DE SELECCIÓN DE PUREZA ---
    elif text in GOLD_TYPES and user_data.get("step") == "select_purity":
        user_data["gold_type"] = text
        user_data["step"] = "input_grams"
        await update.message.reply_text(
            f"✅ Has elegido {text}.\n\nEscriba la cantidad de gramos a calcular:",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Volver"]], resize_keyboard=True)
        )

    # --- LÓGICA DE CÁLCULO FINAL ---
    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.')) # Acepta puntos o comas
            gold_type = user_data["gold_type"]
            ounce_price = get_gold_price_ounce()

            if ounce_price:
                gram_price_24k = ounce_price / 31.1035
                purity = GOLD_TYPES[gold_type]
                total = grams * (gram_price_24k * purity)

                await update.message.reply_text(
                    f"🥇 *Resultado del Cálculo*\n\n"
                    f"Pureza: {gold_type}\n"
                    f"Peso: {grams}g\n"
                    f"Valor total: *${total:,.2f} USD*",
                    parse_mode="Markdown"
                )
                user_data.clear()
                await main_menu(update)
            else:
                await update.message.reply_text("❌ Error al conectar con el servidor de precios.")
        except ValueError:
            await update.message.reply_text("❌ Por favor, introduzca un número válido (ejemplo: 12.5).")

# =========================
# MAIN
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await main_menu(update)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Bot activo (sin soporte)...")
    app.run_polling()

if __name__ == "__main__":
    main()
