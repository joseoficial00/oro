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
USER_NAMES = {ADMIN_ID: "ADMIN"}

USER_MARGINS = {
    ADMIN_ID: 0.88
}

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


def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID


async def deny(update: Update):
    await update.effective_chat.send_message("⛔ NO AUTORIZADO")


# =========================
# ORO API
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
# MENÚ PRINCIPAL (2x2)
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 COTIZAR 🥇", "📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵", "👑 PANEL ADMIN"]
    ]

    if not is_admin(update):
        keyboard[1][1] = "⬜"

    await update.effective_chat.send_message(
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ Bienvenido al cotizador exclusivo.\n\n"
        "👇 Selecciona una opción:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# ADMIN PANEL
# =========================
async def admin_panel(update: Update):

    keyboard = [
        ["➕ AGREGAR USUARIO", "➖ QUITAR USUARIO"],
        ["📊 VER USUARIOS", "💰 CAMBIAR MARGEN"],
        ["⬅️ VOLVER AL MENÚ", "🔙 SALIR ADMIN"]
    ]

    await update.message.reply_text(
        "👑 <b>PANEL ADMIN</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# PUREZA
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
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if not is_authorized(update):
        await deny(update)
        return

    USER_NAMES[uid] = update.effective_user.first_name or "USER"

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
    user_id = update.effective_user.id
    user_data = context.user_data

    dt = datetime.now(TZ_LOUISVILLE)
    fecha = dt.strftime("%d/%m/%Y")
    hora = dt.strftime("%I:%M:%S %p")


    # ================= ADMIN PANEL =================
    if text == "👑 PANEL ADMIN":
        await admin_panel(update)
        return

    # 🔥 FIX: VOLVER DEL ADMIN (ESTO ES LO QUE TE FALLABA)
    if text == "🔙 SALIR ADMIN":
        user_data.clear()
        await main_menu(update)
        return

    if text == "⬅️ VOLVER AL MENÚ":
        user_data.clear()
        await main_menu(update)
        return


    # ================= MENÚ =================
    if text == "🥇 COTIZAR 🥇":
        user_data["step"] = "select"
        await purity_menu(update)
        return


    # ================= COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()
        if price:
            gram = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

            msg = (
f"💵 <b>PRECIO DE COMPRA POR GRAMO</b>\n"
f"📅 <code>{fecha}</code>\n"
f"⏰ <code>{hora}</code>\n\n"
f"🥇 10K: <code>${gram*GOLD_TYPES['10K']*margin:.2f}</code>\n"
f"🥇 14K: <code>${gram*GOLD_TYPES['14K']*margin:.2f}</code>\n"
f"🥇 18K: <code>${gram*GOLD_TYPES['18K']*margin:.2f}</code>\n"
f"🥇 24K: <code>${gram*GOLD_TYPES['24K']*margin:.2f}</code>"
            )

            await update.message.reply_text(msg, parse_mode="HTML")
        return


    # ================= TASA =================
    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()
        if price:
            await update.message.reply_text(
f"📊 <b>TASA EN TIEMPO REAL</b>\n"
f"⏱ {fecha} {hora}\n\n"
f"🪙 1 oz → ${price:,.2f}\n"
f"🥇 1g → ${(price/31.1035):,.2f}",
                parse_mode="HTML"
            )
        return


    # ================= PUREZA =================
    if user_data.get("step") == "select" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "grams"

        await update.message.reply_text(
f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
"✍️ Envíe gramos:",
            parse_mode="HTML"
        )
        return


    # ================= CÁLCULO =================
    if user_data.get("step") == "grams":
        try:
            grams = float(text.replace(",", "."))
            gold_type = user_data["gold_type"]

            price = get_gold_price_ounce()
            if not price:
                return

            gram = price / 31.1035
            total = grams * gram * GOLD_TYPES[gold_type]
            buy = total * USER_MARGINS.get(user_id, 0.88)

            await update.message.reply_text(
f"✨ <b>COTIZACIÓN</b>\n"
f"📅 <code>{fecha}</code>\n"
f"⏰ <code>{hora}</code>\n\n"
f"📦 {gold_type}\n"
f"⚖️ {grams} g\n\n"
f"💰 REAL: ${total:,.2f}\n"
f"🤝 COMPRA: ${buy:,.2f}",
                parse_mode="HTML"
            )

        except:
            await update.message.reply_text("⚠️ Número inválido")


# =========================
# RUN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🚀 BOT ACTIVO")
    app.run_polling()


if __name__ == "__main__":
    main()
