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
# INTERFACES PREMIUM (SIN LÍNEAS)
# ==========================================

async def main_menu(update: Update):
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "💎 *JCS GOLD CALCULATOR | PREMIUM* 💎\n\n"
        "✨ *Bienvenido al cotizador exclusivo.*\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 _Por favor, seleccione una acción del menú:_ 👇"
    )
    await update.effective_chat.send_message(text, reply_markup=reply_markup, parse_mode="Markdown")

async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🌟 22K"],
        ["🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "🏆 *SELECCIÓN DE PUREZA*\n\n"
        "Seleccione el quilataje del oro a evaluar:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==========================================
# GESTIÓN DE PETICIONES
# ==========================================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    now = datetime.now().strftime("%d/%m/%2026  •  %I:%M:%S %p")

    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            msg = (
                f"📊 *TASA OFICIAL EN TIEMPO REAL*\n"
                f"⏱ `{now}`\n\n"
                f"» *Valores de Mercado (XAU/USD):*\n"
                f"🪙 `1 oz (Troy) ` ➜ ` ${price:,.2f} USD `\n"
                f"🥇 `1g Oro (24K)` ➜ ` ${(price / 31.1035):,.2f} USD `\n\n"
                f"⚠️ _La tasa fluctúa según la bolsa internacional._"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No se pudo sincronizar la tasa.")

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
        
        await update.message.reply_text(
            f"👑 *QUILATAJE: {gold_type}*\n\n"
            f"✍️ *Envíe la cantidad de gramos en formato numérico.*\n\n"
            f"💡 _Ejemplos: 10 o 5.75_",
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
                total_real = grams * gram_price
                # Cálculo con 10% menos para tu ganancia
                total_compra = total_real * 0.90
                
                res = (
                    f"✨ *COTIZACIÓN PREMIUM EMITIDA*\n"
                    f"⏱ `{now}`\n\n"
                    f"📦 *Pureza:* `{gold_type}`\n"
                    f"⚖️ *Masa:* `{grams:,} g`\n\n"
                    f"💰 *VALOR REAL:* `${total_real:,.2f} USD`\n"
                    f"🤝 *PRECIO COMPRA:* `${total_compra:,.2f} USD`\n\n"
                    f"✍️ _Puede enviar otro peso o presionar el botón inferior._"
                )
                await update.message.reply_text(res, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Error al obtener precio.")
        except ValueError:
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
