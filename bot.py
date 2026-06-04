import logging
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURACION
# =========================

BOT_TOKEN = "8723973833:AAFmyX4SK3DTE15fFUKu5AiofRS3QaQ2AA4"
GOLD_API_KEY = "goldapi-4ggdsmjfphsjl-io"

# =========================
# LOGS
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =========================
# PUREZA DEL ORO
# =========================

GOLD_TYPES = {
    "10K": 10 / 24,
    "14K": 14 / 24,
    "18K": 18 / 24,
    "22K": 22 / 24,
    "24K": 1.0,
}

# =========================
# OBTENER PRECIO DEL ORO
# =========================

def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"

    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return float(data["price"])
    else:
        return None

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("🥇 Calcular Precio", callback_data="calcular")
        ],
        [
            InlineKeyboardButton("📈 Precio Actual", callback_data="precio")
        ]
    ]

    await update.message.reply_text(
        "Bienvenido al Calculador de Oro",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BOTONES
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "precio":

        price = get_gold_price_ounce()

        if price:
            await query.message.reply_text(
                f"📈 Precio actual del oro:\n\n${price:,.2f} USD por onza"
            )
        else:
            await query.message.reply_text(
                "❌ No se pudo obtener el precio."
            )

    elif query.data == "calcular":

        keyboard = [
            [
                InlineKeyboardButton("10K", callback_data="gold_10K"),
                InlineKeyboardButton("14K", callback_data="gold_14K")
            ],
            [
                InlineKeyboardButton("18K", callback_data="gold_18K"),
                InlineKeyboardButton("22K", callback_data="gold_22K")
            ],
            [
                InlineKeyboardButton("24K", callback_data="gold_24K")
            ]
        ]

        await query.message.reply_text(
            "Seleccione el tipo de oro:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("gold_"):

        gold_type = query.data.replace("gold_", "")

        context.user_data["gold_type"] = gold_type

        await query.message.reply_text(
            f"✅ Seleccionado: {gold_type}\n\n"
            "Ahora escriba los gramos.\n\n"
            "Ejemplo:\n"
            "10.20"
        )

# =========================
# CALCULO
# =========================

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "gold_type" not in context.user_data:
        return

    try:
        grams = float(update.message.text)

        gold_type = context.user_data["gold_type"]

        ounce_price = get_gold_price_ounce()

        if ounce_price is None:
            await update.message.reply_text(
                "❌ Error obteniendo el precio."
            )
            return

        gram_price_24k = ounce_price / 31.1035

        purity = GOLD_TYPES[gold_type]

        gram_price = gram_price_24k * purity

        total = grams * gram_price

        await update.message.reply_text(
            f"🥇 Resultado\n\n"
            f"Tipo: {gold_type}\n"
            f"Gramos: {grams}\n"
            f"Valor: ${total:,.2f} USD"
        )

    except:
        await update.message.reply_text(
            "❌ Introduzca un número válido."
        )

# =========================
# MAIN
# =========================

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT, calculate))

    print("Bot iniciado...")

    app.run_polling()

if __name__ == "__main__":
    main()
