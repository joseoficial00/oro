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
# INTERFACES PREMIUM (REPLY KEYBOARDS)
# ==========================================

async def main_menu(update: Update):
    # Diseño de botones elegante y simétrico
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "💎 *JCS GOLD CALCULATOR | PREMIUM* 💎\n"
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
        ["🏆 24K "],
        ["⬅️ VOLVER AL MENÚ"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "🏆 *SELECCIÓN DE PUREZA*\n"
        "\n"
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

    # --- MENÚ PRINCIPAL: TASA EN TIEMPO REAL ---
    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            msg = (
                f"📊 *TASA OFICIAL EN TIEMPO REAL*\n"
                f"⏱ `{now}`\n"
                f"» *Valores de Mercado (XAU/USD):*\n"
                f"🪙 `1 oz (Troy) ` ➜ ` ${price:,.2f} USD `\n"
                f"🥇 `1g Oro (24K)` ➜ ` ${(price / 31.1035):,.2f} USD `\n\n"
                f"⚠️ _La tasa fluctúa según la bolsa internacional._"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Error transitorio:* No se pudo sincronizar la tasa. Intente de nuevo.", parse_mode="Markdown")

    # --- MENÚ PRINCIPAL: EMPEZAR CÁLCULO ---
    elif text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    # --- BOTÓN DE RETORNO ---
    elif text in ["⬅️ VOLVER AL MENÚ", "⬅️ VOLVER"]:
        user_data.clear()
        await main_menu(update)

    # --- PASO: CAPTURAR QUILATES ---
    elif user_data.get("step") == "select_purity" and any(q in text for q in GOLD_TYPES):
        # Limpiar emojis del texto seleccionado para extraer el quilataje (ej: "⚡ 14K" -> "14K")
        gold_type = next(q for q in GOLD_TYPES if q in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"
        
        await update.message.reply_text(
            f"👑 *QUILATAJE SELECCIONADO: {gold_type}*\n"
            f"✍️ *Envíe la cantidad de gramos en formato numérico.*\n\n"
            f"💡 _Ejemplos: 10 o 5.75_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([["⬅️ VOLVER"]], resize_keyboard=True)
        )

    # --- PASO: CAPTURAR GRAMOS Y CALCULAR (SIN REINICIAR) ---
    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.'))
            gold_type = user_data["gold_type"]
            price = get_gold_price_ounce()
            
            if price:
                gram_price = (price / 31.1035) * GOLD_TYPES[gold_type]
                total = grams * gram_price
                
                res = (
                    f"✨ *COTIZACIÓN PREMIUM EMITIDA*\n"
                    f"⏱ `{now}`\n"
                    f"📦 *Pureza:* `{gold_type}`\n"
                    f"⚖️ *Masa Evaluada:* `{grams:,} g`\n"
                    f"💵 *Precio por Gramo:* `${gram_price:,.2f} USD`\n\n"
                    f"💰 *VALOR ESTIMADO:* \n"
                    f"➜ ` ${total:,.2f} USD `\n"
                    f\n"
                    f"✍️ _Si desea calcular otro peso con {gold_type}, introduzca los gramos directamente. Si prefiere cambiar de opción, presione el botón inferior._"
                )
                await update.message.reply_text(res, parse_mode="Markdown")
                # NOTA: No hacemos user_data.clear() para permitir cálculos seguidos con el mismo quilate.
            else:
                await update.message.reply_text("❌ Error al obtener la cotización. Intente nuevamente.")
        except ValueError:
            await update.message.reply_text("⚠️ *Formato incorrecto.* Por favor, introduzca únicamente un número válido.")

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
