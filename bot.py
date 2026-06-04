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

# ==========================================
# CONFIGURACIÓN
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8723973833:AAFmyX4SK3DTE15fFUKu5AiofRS3QaQ2AA4")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "goldapi-4ggdsmjfphsjl-io")

logging.basicConfig(level=logging.INFO)

GOLD_TYPES = {
    "10K": 10 / 24, "14K": 14 / 24, "18K": 18 / 24, "22K": 22 / 24, "24K": 1.0,
}

CUSTOM_EMOJI = "5917773753390994274"

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

# ==========================================
# INTERFACES
# ==========================================

async def main_menu(update: Update):
    keyboard = [["🥇 CALCULAR VALOR 🥇"], ["📈 TASA EN TIEMPO REAL 💸"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    text = (
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n\n"
        "👇 <i>Por favor, seleccione una acción:</i>"
    )
    await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode="HTML")

async def purity_menu(update: Update):
    keyboard = [["⚡ 10K", "⚡ 14K"], ["🌟 18K", "🌟 22K"], ["🏆 24K (Puro)"], ["⬅️ VOLVER"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("<b>🏆 SELECCIÓN DE PUREZA</b>\n\nElija el quilataje:", reply_markup=reply_markup, parse_mode="HTML")

# ==========================================
# GESTIÓN DE PETICIONES
# ==========================================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    
    # Formato de fecha y hora mejorado
    fecha = datetime.now().strftime("%d / %m / 2026")
    hora = datetime.now().strftime("%I:%M:%S %p")

    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            msg = (
                f"📊 <b>TASA EN TIEMPO REAL</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"🪙 <code>Oz Troy: </code> ➜ <code> ${price:,.2f} USD </code>\n"
                f"🥇 <code>1g (24K): </code> ➜ <code> ${(price / 31.1035):,.2f} USD </code>"
            )
            await update.message.reply_text(msg, parse_mode="HTML")

    elif text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    elif text == "⬅️ VOLVER":
        user_data.clear()
        await main_menu(update)

    elif user_data.get("step") == "select_purity" and any(q in text for q in GOLD_TYPES):
        gold_type = next(q for q in GOLD_TYPES if q in text)
        user_data.update({"gold_type": gold_type, "step": "input_grams"})
        await update.message.reply_text(f"👑 <b>QUILATAJE: {gold_type}</b>\n\n✍️ <b>Envíe los gramos:</b>", parse_mode="HTML")

    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.'))
            price = get_gold_price_ounce()
            if price:
                gram_price = (price / 31.1035) * GOLD_TYPES[user_data["gold_type"]]
                total_real = grams * gram_price
                total_compra = total_real * 0.90 # Margen 10%
                
                res = (
                    f"<tg-emoji emoji-id='{CUSTOM_EMOJI}'>✨</tg-emoji> <b>COTIZACIÓN</b>\n"
                    f"📅 <code>{fecha}</code>\n"
                    f"⏰ <code>{hora}</code>\n\n"
                    f"📦 <b>Quilate:</b> <code>{user_data['gold_type']}</code>\n"
                    f"⚖️ <b>Peso:</b> <code>{grams:,} g</code>\n\n"
                    f"💰 <b>VALOR REAL:</b> <code>${total_real:,.2f} USD</code>\n"
                    f"🤝 <b>PRECIO COMPRA:</b> <code>${total_compra:,.2f} USD</code>\n\n"
                    f"✍️ <i>Envíe otro peso o presione Volver.</i>"
                )
                await update.message.reply_text(res, parse_mode="HTML")
        except:
            await update.message.reply_text("⚠️ Envíe solo números.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data.clear()
    await main_menu(update)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == "__main__":
    main()
    
