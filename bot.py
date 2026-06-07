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

BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_BOT_TOKEN_AQUÍ")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "TU_API_KEY_AQUÍ")

# IDs autorizados
AUTHORIZED_USERS = {
    6794562791,  # Tu ID
    987654321,  # Otro usuario autorizado
}

logging.basicConfig(level=logging.INFO)

GOLD_TYPES = {
    "10K": 10 / 24,
    "14K": 14 / 24,
    "18K": 18 / 24,
    "24K": 1.0,
}

TZ_LOUISVILLE = ZoneInfo("America/Kentucky/Louisville")


def is_authorized(update: Update):
    return update.effective_user.id in AUTHORIZED_USERS


async def access_denied(update: Update):
    await update.effective_chat.send_message(
        "⛔ ACCESO DENEGADO\n\n"
        "No tienes autorización para utilizar este bot."
    )


def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return float(response.json()["price"])

        return None

    except Exception:
        return None


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

    text = (
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Seleccione una opción:</i>"
    )

    await update.effective_chat.send_message(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K"],
        ["🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "<b>🏆 SELECCIÓN DE PUREZA</b>\n\nSeleccione el quilataje:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update):
        await access_denied(update)
        return

    context.user_data.clear()
    await main_menu(update)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update):
        await access_denied(update)
        return

    text = update.message.text
    user_data = context.user_data

    dt_now = datetime.now(TZ_LOUISVILLE)
    fecha = dt_now.strftime("%d/%m/%Y")
    hora = dt_now.strftime("%I:%M:%S %p")

    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if price:

            gram_price_24k = price / 31.1035

            msg = (
                f"💵 <b>PRECIO DE COMPRA POR GRAMO</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"🥇 <b>10K:</b> <code>${gram_price_24k * GOLD_TYPES['10K'] * 0.88:.2f}/g</code>\n"
                f"🥇 <b>14K:</b> <code>${gram_price_24k * GOLD_TYPES['14K'] * 0.88:.2f}/g</code>\n"
                f"🥇 <b>18K:</b> <code>${gram_price_24k * GOLD_TYPES['18K'] * 0.88:.2f}/g</code>\n"
                f"🥇 <b>24K:</b> <code>${gram_price_24k * GOLD_TYPES['24K'] * 0.88:.2f}/g</code>"
            )

            await update.message.reply_text(
                msg,
                parse_mode="HTML"
            )

        else:
            await update.message.reply_text(
                "❌ No se pudo obtener el precio actual."
            )

        return

    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()

        if price:

            msg = (
                f"📊 <b>TASA OFICIAL EN TIEMPO REAL</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"🪙 <code>1 oz Troy</code> ➜ "
                f"<code>${price:,.2f} USD</code>\n"
                f"🥇 <code>1g Oro 24K</code> ➜ "
                f"<code>${(price / 31.1035):,.2f} USD</code>"
            )

            await update.message.reply_text(
                msg,
                parse_mode="HTML"
            )

        else:
            await update.message.reply_text(
                "❌ No se pudo sincronizar la tasa actual."
            )

        return

    if text == "🥇 CALCULAR VALOR 🥇":

        user_data["step"] = "select_purity"
        await purity_menu(update)
        return

    if text in ["⬅️ VOLVER AL MENÚ", "⬅️ VOLVER"]:

        user_data.clear()
        await main_menu(update)
        return

    if (
        user_data.get("step") == "select_purity"
        and any(q in text for q in GOLD_TYPES)
    ):

        gold_type = next(
            q for q in GOLD_TYPES if q in text
        )

        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"

        await update.message.reply_text(
            f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ Envíe los gramos.\n\n"
            f"💡 Ejemplo: 10 o 5.75",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ VOLVER"]],
                resize_keyboard=True
            )
        )

        return

    if user_data.get("step") == "input_grams":

        try:

            grams = float(text.replace(",", "."))
            gold_type = user_data["gold_type"]

            price = get_gold_price_ounce()

            if not price:
                await update.message.reply_text(
                    "❌ Error al obtener precio del mercado."
                )
                return

            gram_price_24k = price / 31.1035
            gram_price_selected = (
                gram_price_24k *
                GOLD_TYPES[gold_type]
            )

            total_real = grams * gram_price_selected
            total_compra = total_real * 0.88

            msg = (
                f"✨ <b>COTIZACIÓN</b>\n\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"📦 <b>Quilate:</b> <code>{gold_type}</code>\n"
                f"⚖️ <b>Peso:</b> <code>{grams} g</code>\n\n"
                f"💰 <b>VALOR REAL:</b>\n"
                f"<code>${total_real:,.2f} USD</code>\n\n"
                f"🤝 <b>PRECIO COMPRA:</b>\n"
                f"<code>${total_compra:,.2f} USD</code>"
            )

            await update.message.reply_text(
                msg,
                parse_mode="HTML"
            )

        except ValueError:

            await update.message.reply_text(
                "⚠️ Introduzca un número válido.\n"
                "Ejemplo: 12.5"
            )


def main():

    app = Application.builder().token(BOT_TOKEN).build()

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
