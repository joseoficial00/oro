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
# Se recomienda usar variables de entorno por seguridad
BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_BOT_TOKEN_AQUÍ")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "TU_API_KEY_AQUÍ")

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
        else:
            logging.error(f"Error API Oro: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error de conexión: {e}")
        return None

# ==========================================
# INTERFACES PREMIUM (HTML)
# ==========================================

async def main_menu(update: Update):
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Por favor, seleccione una acción del menú:</i> 👇"
    )
    await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode="HTML")

async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🌟 22K"],
        ["🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "<b>🏆 SELECCIÓN DE PUREZA</b>\n\n"
        "Seleccione el quilataje del oro a evaluar:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

# ==========================================
# GESTIÓN DE PETICIONES
# ==========================================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    
    # Arreglo de fecha y hora
    dt_now = datetime.now()
    fecha = dt_now.strftime("%d/%m/%2026")
    hora = dt_now.strftime("%I:%M:%S %p")

    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            msg = (
                f"📊 <b>TASA OFICIAL EN TIEMPO REAL</b>\n"
                f"⏱ <code>{fecha} • {hora}</code>\n\n"
                f"» <b>Valores de Mercado (XAU/USD):</b>\n"
                f"🪙 <code>1 oz (Troy) </code> ➜ <code> ${price:,.2f} USD </code>\n"
                f"🥇 <code>1g Oro (24K)</code> ➜ <code> ${(price / 31.1035):,.2f} USD </code>\n\n"
                f"⚠️ <i>La tasa fluctúa según la bolsa internacional.</i>"
            )
            await update.message.reply_text(msg, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ No se pudo sincronizar la tasa actual.")

    elif text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    elif text in ["⬅️ VOLVER AL MENÚ", "⬅️ VOLVER"]:
        user_data.clear()
        await main_menu(update)

    elif user_data.get("step") == "select_purity" and any(q in text for q in GOLD_TYPES):
        gold_type = next(q for q in GOLD_TYPES if q in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"
        
        await update.message.reply_text(f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ <b>Envíe la cantidad de gramos en formato numérico.</b>\n\n"
            f"💡 <i>Ejemplos: 10 o 5.75</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["⬅️ VOLVER"]], resize_keyboard=True)
        )

    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.'))
            gold_type = user_data["gold_type"]
            price = get_gold_price_ounce()
            
            if price:
                # 31.1035 es la conversión de Onza Troy a Gramos
                gram_price_24k = price / 31.1035
                gram_price_selected = gram_price_24k * GOLD_TYPES[gold_type]
                
                total_real = grams * gram_price_selected
                total_compra = total_real * 0.90 # 10% de comisión
                
                res = (
                    f"<tg-emoji emoji-id='{CUSTOM_EMOJI}'>✨</tg-emoji> <b>COTIZACIÓN</b>\n"
                    f"📅 <code>{fecha}</code>\n"
                    f"⏰ <code>{hora}</code>\n\n"
                    f"📦 <b>Quilate:</b> <code>{gold_type}</code>\n"
                    f"⚖️ <b>Peso:</b> <code>{grams:,} g</code>\n\n"
                    f"💰 <b>VALOR REAL:</b> <code>${total_real:,.2f} USD</code>\n"
                    f"🤝 <b>PRECIO COMPRA (Neto):</b> <code>${total_compra:,.2f} USD</code>\n\n"
                    f"✍️ <i>Envíe otro peso o presione Volver.</i>"
                )
                await update.message.reply_text(res, parse_mode="HTML")
            else:
                await update.message.reply_text("❌ Error al obtener precio del mercado.")
        except ValueError:
            await update.message.reply_text("⚠️ Por favor, envíe un número válido (ej: 12.5).")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await main_menu(update)

def main():
    # Crea la aplicación con el token
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Manejadores
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("Bot en marcha...")
    app.run_polling()

if name == "__main__":
    main()
