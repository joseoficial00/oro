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
# 🔑 CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_BOT_TOKEN_AQUÍ")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "TU_API_KEY_AQUÍ")

ADMIN_ID = 6794562791

AUTHORIZED_USERS = {ADMIN_ID}
USER_NAMES = {ADMIN_ID: "ADMIN"}
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
# 🔐 ACCESO
# =========================
def is_authorized(update: Update):
    return update.effective_user.id in AUTHORIZED_USERS


def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID


async def deny(update: Update):
    await update.message.reply_text("⛔ NO AUTORIZADO")


# =========================
# 💰 API ORO (FIX)
# =========================
def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)

        logging.info(f"GoldAPI status: {r.status_code}")
        logging.info(f"GoldAPI response: {r.text}")

        if r.status_code == 200:
            data = r.json()
            return float(data.get("price", 0))

        return None

    except Exception as e:
        logging.error(f"Gold API error: {e}")
        return None


# =========================
# 📋 MENÚ
# =========================
async def main_menu(update: Update):

    keyboard = [
        ["🥇 COTIZAR 🥇", "📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵", "👑 PANEL ADMIN"]
    ]

    if not is_admin(update):
        keyboard[1][1] = "⬜"

    await update.message.reply_text(
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ Bienvenido al cotizador.\n"
        "👇 Selecciona una opción 👇",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 🏆 PUREZA
# =========================
async def purity_menu(update: Update):

    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    await update.message.reply_text(
        "<b>🏆 SELECCIÓN DE PUREZA</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 👑 ADMIN
# =========================
async def admin_panel(update: Update):

    keyboard = [
        ["➕ AGREGAR USUARIO", "➖ QUITAR USUARIO"],
        ["✏️ EDITAR USUARIO", "📊 VER USUARIOS"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    await update.message.reply_text(
        "👑 <b>PANEL ADMIN</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 🚀 START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update):
        await deny(update)
        return

    context.user_data.clear()
    await main_menu(update)


# =========================
# 💬 MENSAJES
# =========================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update):
        await deny(update)
        return

    text = update.message.text
    user_id = update.effective_user.id
    data = context.user_data

    dt = datetime.now(TZ_LOUISVILLE)
    fecha = dt.strftime("%d/%m/%Y")
    hora = dt.strftime("%I:%M:%S %p")

    # ================= MENÚ =================
    if text == "⬅️ VOLVER AL MENÚ":
        data.clear()
        await main_menu(update)
        return

    if text == "🥇 COTIZAR 🥇":
        data["step"] = "select"
        await purity_menu(update)
        return

    # ================= TASA EN TIEMPO REAL =================
    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()

        if price is not None:
            gram = price / 31.1035

            await update.message.reply_text(
                f"📊 <b>TASA EN TIEMPO REAL</b>\n"
                f"⏱ {fecha} {hora}\n\n"
                f"🪙 1 oz → ${price:,.2f}\n"
                f"🥇 1g → ${gram:,.2f}",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "⚠️ No se pudo obtener la tasa del oro."
            )
        return

    # ================= PRECIO COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if price is None:
            await update.message.reply_text("⚠️ Error obteniendo precio del oro.")
            return

        gram = price / 31.1035
        margin = USER_MARGINS.get(user_id, 0.88)

        msg = (
            f"💵 <b>PRECIO DE COMPRA</b>\n"
            f"📅 {fecha}\n"
            f"⏰ {hora}\n\n"
            f"🥇 10K: ${gram*GOLD_TYPES['10K']*margin:.2f}\n"
            f"🥇 14K: ${gram*GOLD_TYPES['14K']*margin:.2f}\n"
            f"🥇 18K: ${gram*GOLD_TYPES['18K']*margin:.2f}\n"
            f"🥇 24K: ${gram*GOLD_TYPES['24K']*margin:.2f}"
        )

        await update.message.reply_text(msg, parse_mode="HTML")
        return

    # ================= PUREZA =================
    if data.get("step") == "select" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        data["gold_type"] = gold_type
        data["step"] = "grams"

        await update.message.reply_text(
            f"✍️ Envía gramos para {gold_type}",
            parse_mode="HTML"
        )
        return

    if data.get("step") == "grams":
        try:
            grams = float(text.replace(",", "."))
            gold_type = data["gold_type"]

            price = get_gold_price_ounce()
            if price is None:
                await update.message.reply_text("⚠️ Error de API.")
                return

            gram = price / 31.1035
            total = grams * gram * GOLD_TYPES[gold_type]
            buy = total * USER_MARGINS.get(user_id, 0.88)

            await update.message.reply_text(
                f"✨ <b>COTIZACIÓN</b>\n\n"
                f"📦 {gold_type}\n"
                f"⚖️ {grams} g\n\n"
                f"💰 Valor: ${total:,.2f}\n"
                f"🤝 Compra: ${buy:,.2f}",
                parse_mode="HTML"
            )

        except:
            await update.message.reply_text("⚠️ Número inválido")
        return


# =========================
# 🚀 RUN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🚀 BOT ACTIVO")
    app.run_polling()


if __name__ == "__main__":
    main()
