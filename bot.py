```python
import logging
import requests
import os
from datetime import datetime
from zoneinfo import ZoneInfo

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

BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_BOT_TOKEN_AQUI")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "TU_API_KEY_AQUI")

logging.basicConfig(level=logging.INFO)

TZ_LOUISVILLE = ZoneInfo("America/Kentucky/Louisville")

GOLD_TYPES = {
    "10K": 10 / 24,
    "14K": 14 / 24,
    "18K": 18 / 24,
    "24K": 1.0,
}

# ==========================================
# PRECIO ORO
# ==========================================

def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"

    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return float(data["price"])

        logging.error(
            f"GoldAPI Error {response.status_code}: {response.text}"
        )
        return None

    except Exception as e:
        logging.error(f"Error conexión API: {e}")
        return None

# ==========================================
# MENÚ PRINCIPAL
# ==========================================

async def main_menu(update: Update):

    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    mensaje = (
        "<b>💎 JCS GOLD CALCULATOR 💎</b>\n\n"
        "🌎 Conectado al mercado internacional.\n"
        "⚡ Cotización actualizada en tiempo real.\n"
        "📊 Cálculos automáticos.\n\n"
        "👇 Seleccione una opción:"
    )

    await update.effective_chat.send_message(
        mensaje,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ==========================================
# MENÚ QUILATES
# ==========================================

async def purity_menu(update: Update):

    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🏆 24K"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "<b>Seleccione el quilataje:</b>",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ==========================================
# START
# ==========================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()
    await main_menu(update)

# ==========================================
# MENSAJES
# ==========================================

async def handle_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()
    user_data = context.user_data

    now = datetime.now(TZ_LOUISVILLE)

    fecha = now.strftime("%d/%m/%Y")
    hora = now.strftime("%I:%M:%S %p")

    # ==========================
    # PRECIO DE COMPRA
    # ==========================

    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if not price:
            await update.message.reply_text(
                "❌ No se pudo obtener el precio del oro."
            )
            return

        gram_24k = price / 31.1035

        precio_10k = gram_24k * GOLD_TYPES["10K"] * 0.88
        precio_14k = gram_24k * GOLD_TYPES["14K"] * 0.88
        precio_18k = gram_24k * GOLD_TYPES["18K"] * 0.88
        precio_24k = gram_24k * GOLD_TYPES["24K"] * 0.88

        mensaje = (
            f"💵 <b>PRECIO DE COMPRA POR GRAMO</b>\n\n"
            f"📅 {fecha}\n"
            f"⏰ {hora}\n\n"
            f"🥇 10K ➜ <code>${precio_10k:.2f}</code>\n"
            f"🥇 14K ➜ <code>${precio_14k:.2f}</code>\n"
            f"🥇 18K ➜ <code>${precio_18k:.2f}</code>\n"
            f"🥇 24K ➜ <code>${precio_24k:.2f}</code>\n\n"
            f"📉 Incluye descuento del 12%."
        )

        await update.message.reply_text(
            mensaje,
            parse_mode="HTML"
        )

    # ==========================
    # TASA TIEMPO REAL
    # ==========================

    elif text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()

        if not price:
            await update.message.reply_text(
                "❌ No se pudo obtener la tasa."
            )
            return

        gram_price = price / 31.1035

        mensaje = (
            f"📈 <b>TASA EN TIEMPO REAL</b>\n\n"
            f"📅 {fecha}\n"
            f"⏰ {hora}\n\n"
            f"🪙 Onza Troy ➜ "
            f"<code>${price:,.2f}</code>\n\n"
            f"🥇 Oro 24K / gr ➜ "
            f"<code>${gram_price:,.2f}</code>"
        )

        await update.message.reply_text(
            mensaje,
            parse_mode="HTML"
        )

    # ==========================
    # CALCULAR
    # ==========================

    elif text == "🥇 CALCULAR VALOR 🥇":

        user_data["step"] = "purity"

        await purity_menu(update)

    elif text in ["⬅️ VOLVER", "⬅️ VOLVER AL MENÚ"]:

        user_data.clear()

        await main_menu(update)

    elif (
        user_data.get("step") == "purity"
        and any(k in text for k in GOLD_TYPES)
    ):

        quilate = next(
            k for k in GOLD_TYPES
            if k in text
        )

        user_data["gold_type"] = quilate
        user_data["step"] = "grams"

        await update.message.reply_text(
            f"🥇 Quilataje seleccionado: "
            f"<b>{quilate}</b>\n\n"
            f"✍️ Escriba los gramos:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ VOLVER"]],
                resize_keyboard=True
            )
        )

    elif user_data.get("step") == "grams":

        try:

            gramos = float(
                text.replace(",", ".")
            )

            quilate = user_data["gold_type"]

            price = get_gold_price_ounce()

            if not price:
                await update.message.reply_text(
                    "❌ No se pudo obtener el precio."
                )
                return

            gram_24k = price / 31.1035

            gram_selected = (
                gram_24k *
                GOLD_TYPES[quilate]
            )

            valor_real = gramos * gram_selected

            precio_compra = valor_real * 0.88

            mensaje = (
                f"✨ <b>COTIZACIÓN</b>\n\n"
                f"📅 {fecha}\n"
                f"⏰ {hora}\n\n"
                f"🥇 Quilate: {quilate}\n"
                f"⚖️ Peso: {gramos} g\n\n"
                f"💰 Valor Real:\n"
                f"<code>${valor_real:,.2f}</code>\n\n"
                f"🤝 Precio Compra:\n"
                f"<code>${precio_compra:,.2f}</code>\n\n"
                f"📉 Descuento aplicado: 12%"
            )

            await update.message.reply_text(
                mensaje,
                parse_mode="HTML"
            )

        except ValueError:

            await update.message.reply_text(
                "⚠️ Introduzca un número válido.\n"
                "Ejemplo: 12.5"
            )

# ==========================================
# MAIN
# ==========================================

def main():

    if BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        print("Configure BOT_TOKEN")
        return

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_messages
        )
    )

    print("Bot iniciado correctamente...")

    app.run_polling()

if __name__ == "__main__":
    main()
```
