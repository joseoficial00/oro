import logging
import requests
import os
from datetime import datetime
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
BOT_TOKEN = os.getenv("BOT_TOKEN", "8723973833:AAFmyX4SK3DTE15fFUKu5AiofRS3QaQ2AA4")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "goldapi-4ggdsmjfphsjl-io")

logging.basicConfig(level=logging.INFO)

GOLD_TYPES = {
    "10K": 10 / 24, "14K": 14 / 24, "18K": 18 / 24, "22K": 22 / 24, "24K": 1.0,
}

def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return float(response.json()["price"])
    except:
        return None
    return None

# =========================
# DISEÑO DE MENÚS (ESTILO FOTO)
# =========================

async def main_menu(update: Update):
    # Botones organizados como en la segunda foto
    keyboard = [
        ["🥇 CALCULAR PRECIO 🥇"],
        ["📈 PRECIO ACTUAL", "⬅️ VOLVER"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "💸 *JCS GOLD CALCULATOR*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔥 *Servicio rápido y preciso*\n"
        "📊 Cotización en tiempo real\n"
        "💰 Valor de mercado actualizado\n\n"
        "Seleccione una opción del menú 👇"
    )
    await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode="Markdown")

async def purity_menu(update: Update):
    # Botones de pureza en cuadrícula
    keyboard = [
        ["10K", "14K"],
        ["18K", "22K"],
        ["24K"],
        ["⬅️ VOLVER"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "🥇 *TIPO DE ORO*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Seleccione la pureza para calcular:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# =========================
# LÓGICA DE MENSAJES
# =========================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    now = datetime.now().strftime("%d/%m/%2026 %I:%M:%S %p")

    if text == "📈 PRECIO ACTUAL":
        price = get_gold_price_ounce()
        if price:
            msg = (
                f"📊 *Tasa en tiempo real*\n"
                f"⏱ {now}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"» *Valores actuales del mercado:*\n"
                f"🥇 Oro (24K) → ${price:,.2f} USD\n"
                f"⚖️ Onza Troy → 31.1035g\n\n"
                f"❗ *Nota:* El precio base es en USD/oz."
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No se pudo conectar con la tasa.")

    elif text == "🥇 CALCULAR PRECIO 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    elif text == "⬅️ VOLVER":
        user_data.clear()
        await main_menu(update)

    elif text in GOLD_TYPES and user_data.get("step") == "select_purity":
        user_data["gold_type"] = text
        user_data["step"] = "input_grams"
        await update.message.reply_text(
            f"✅ *Seleccionado:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✍️ Escriba la cantidad de gramos ahora:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([["⬅️ VOLVER"]], resize_keyboard=True)
        )

    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.'))
            gold_type = user_data["gold_type"]
            price = get_gold_price_ounce()
            if price:
                gram_price = (price / 31.1035) * GOLD_TYPES[gold_type]
                total = grams * gram_price
                
                res = (
                    f"🥇 *RESULTADO DEL CÁLCULO*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📦 *Tipo:* {gold_type}\n"
                    f"⚖️ *Peso:* {grams}g\n"
                    f"💰 *Total:* ${total:,.2f} USD\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Cálculo finalizado."
                )
                await update.message.reply_text(res, parse_mode="Markdown")
                user_data.clear()
                await main_menu(update)
        except:
            await update.message.reply_text("❌ Introduzca un número válido.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == "__main__":
    main()
