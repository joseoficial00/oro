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

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_BOT_TOKEN_AQUÍ")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "TU_API_KEY_AQUÍ")

ADMIN_ID = 6794562791

AUTHORIZED_USERS = {ADMIN_ID}

USER_MARGINS = {ADMIN_ID: 0.88}

logging.basicConfig(level=logging.INFO)

GOLD_TYPES = {
    "10K": 10 / 24,
    "14K": 14 / 24,
    "18K": 18 / 24,
    "24K": 1.0,
}

TZ_LOUISVILLE = ZoneInfo("America/Kentucky/Louisville")


# =========================
# ACCESO
# =========================
def is_authorized(update: Update):
    return update.effective_user.id in AUTHORIZED_USERS

async def deny(update: Update):
    await update.effective_chat.send_message("⛔ NO AUTORIZADO")


# =========================
# API ORO
# =========================
def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": GOLD_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return float(r.json()["price"])
        return None
    except:
        return None


# =========================
# MENÚ PRINCIPAL (TU MENSAJE)
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵"]
    ]

    text = (
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Por favor, seleccione una acción del menú:</i> 👇"
    )

    await update.effective_chat.send_message(
        text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# PUREZA MENU (TU MENSAJE)
# =========================
async def purity_menu(update: Update, gold_type=""):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    text = (
        "<b>🏆 SELECCIÓN DE PUREZA</b>\n\n"
        "Seleccione el quilataje del oro a evaluar:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await deny(update)
        return

    context.user_data.clear()
    await main_menu(update)


# =========================
# MENSAJES
# =========================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update):
        await deny(update)
        return

    text = update.message.text
    user_data = context.user_data

    dt = datetime.now(TZ_LOUISVILLE)
    fecha = dt.strftime("%d/%m/%Y")
    hora = dt.strftime("%I:%M:%S %p")

    # ================= MENU =================
    if text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select"
        await purity_menu(update)
        return

    if text == "⬅️ VOLVER AL MENÚ":
        user_data.clear()
        await main_menu(update)
        return

    # ================= PUREZA SELECCIÓN (TU MENSAJE EXACTO) =================
    if user_data.get("step") == "select" and any(k in text for k in GOLD_TYPES):

        gold_type = next(k for k in GOLD_TYPES if k in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "grams"

        await update.message.reply_text(
            f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ <b>Envíe la cantidad de gramos en formato numérico.</b>\n\n"
            f"💡 <i>Ejemplos: 10 o 5.75</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["⬅️ VOLVER AL MENÚ"]], resize_keyboard=True)
        )
        return

    # ================= CÁLCULO (TU MENSAJE EXACTO) =================
    if user_data.get("step") == "grams":

        try:
            grams = float(text.replace(",", "."))
            gold_type = user_data["gold_type"]

            price = get_gold_price_ounce()
            if not price:
                return

            gram_price = (price / 31.1035) * GOLD_TYPES[gold_type]

            total_real = grams * gram_price
            total_compra = total_real * USER_MARGINS.get(ADMIN_ID, 0.88)

            await update.message.reply_text(
                f"✨ <b>COTIZACIÓN</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"📦 <b>Quilate:</b> <code>{gold_type}</code>\n"
                f"⚖️ <b>Peso:</b> <code>{grams:,} g</code>\n\n"
                f"💰 <b>VALOR REAL:</b> <code>${total_real:,.2f} USD</code>\n"
                f"🤝 <b>PRECIO COMPRA (Neto):</b> <code>${total_compra:,.2f} USD</code>\n\n"
                f"✍️ <i>Envíe otro peso o presione Volver.</i>",
                parse_mode="HTML"
            )

        except ValueError:
            await update.message.reply_text("⚠️ Número inválido")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🚀 BOT ACTIVO")
    app.run_polling()


if __name__ == "__main__":
    main()
