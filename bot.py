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

# 👇 usuarios autorizados (ID: nombre)
AUTHORIZED_USERS = {
    ADMIN_ID: "ADMIN"
}

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
# 🔐 ACCESO
# =========================
def is_authorized(update: Update):
    return update.effective_user.id in AUTHORIZED_USERS

def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID

async def deny(update: Update):
    await update.effective_chat.send_message("⛔ NO AUTORIZADO")


# =========================
# 💰 API ORO
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
# 📋 MENÚ PRINCIPAL
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 COTIZAR 🥇", "📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵"]
    ]

    if is_admin(update):
        keyboard.append(["👑 PANEL ADMIN"])

    await update.effective_chat.send_message(
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ Bienvenido al cotizador exclusivo.\n"
        "👇 Selecciona una opción:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 🏆 PUREZA MENU
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
# 👑 PANEL ADMIN
# =========================
async def admin_panel(update: Update):
    keyboard = [
        ["➕ AGREGAR USUARIO", "➖ QUITAR USUARIO"],
        ["📊 VER USUARIOS"],
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
    user_name = update.effective_user.first_name

    dt = datetime.now(TZ_LOUISVILLE)
    fecha = dt.strftime("%d/%m/%Y")
    hora = dt.strftime("%I:%M:%S %p")

    # ================= ADMIN PANEL =================
    if text == "👑 PANEL ADMIN":
        if not is_admin(update):
            await deny(update)
            return
        await admin_panel(update)
        return

    # ================= AGREGAR USUARIO =================
    if text == "➕ AGREGAR USUARIO":
        context.user_data["admin_action"] = "add"
        await update.message.reply_text("Envía ID del usuario:")
        return

    if text == "➖ QUITAR USUARIO":
        context.user_data["admin_action"] = "remove"
        await update.message.reply_text("Envía ID del usuario:")
        return

    if context.user_data.get("admin_action") == "add" and is_admin(update):
        try:
            uid = int(text)
            AUTHORIZED_USERS[uid] = f"User_{uid}"
            USER_MARGINS.setdefault(uid, 0.88)
            await update.message.reply_text(f"✅ Usuario {uid} agregado")
        except:
            await update.message.reply_text("❌ ID inválido")
        return

    if context.user_data.get("admin_action") == "remove" and is_admin(update):
        try:
            uid = int(text)
            AUTHORIZED_USERS.pop(uid, None)
            USER_MARGINS.pop(uid, None)
            await update.message.reply_text(f"❌ Usuario {uid} eliminado")
        except:
            await update.message.reply_text("❌ Error")
        return

    if text == "📊 VER USUARIOS":
        msg = "👥 USUARIOS AUTORIZADOS:\n\n"
        for uid, name in AUTHORIZED_USERS.items():
            msg += f"{name} | ID: {uid}\n"
        await update.message.reply_text(msg)
        return

    # ================= PRECIO COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()
        if price:
            gram_price = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

            msg = (
                f"💵 <b>PRECIO DE COMPRA</b>\n"
                f"📅 {fecha}\n⏰ {hora}\n\n"
                f"🥇 10K: ${(gram_price * GOLD_TYPES['10K'] * margin):.2f}\n"
                f"🥇 14K: ${(gram_price * GOLD_TYPES['14K'] * margin):.2f}\n"
                f"🥇 18K: ${(gram_price * GOLD_TYPES['18K'] * margin):.2f}\n"
                f"🥇 24K: ${(gram_price * GOLD_TYPES['24K'] * margin):.2f}"
            )

            await update.message.reply_text(msg, parse_mode="HTML")
        return

    # ================= TASA =================
    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()
        if price:
            await update.message.reply_text(
                f"📊 TASA\n{fecha} {hora}\n\n"
                f"🪙 1oz: ${price:,.2f}\n"
                f"🥇 1g: ${(price / 31.1035):,.2f}"
            )
        return

    # ================= COTIZAR =================
    if text == "🥇 COTIZAR 🥇":
        context.user_data["step"] = "select"
        await purity_menu(update)
        return

    if text == "⬅️ VOLVER AL MENÚ":
        context.user_data.clear()
        await main_menu(update)
        return

    if context.user_data.get("step") == "select" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        context.user_data["gold_type"] = gold_type
        context.user_data["step"] = "grams"

        await update.message.reply_text("Envía gramos:")
        return

    if context.user_data.get("step") == "grams":
        try:
            grams = float(text.replace(",", "."))
            gold_type = context.user_data["gold_type"]

            price = get_gold_price_ounce()
            if not price:
                return

            gram_price = (price / 31.1035) * GOLD_TYPES[gold_type]

            total = grams * gram_price
            buy = total * USER_MARGINS.get(user_id, 0.88)

            await update.message.reply_text(
                f"✨ COTIZACIÓN\n"
                f"{fecha} {hora}\n\n"
                f"{gold_type} | {grams}g\n\n"
                f"💰 REAL: ${total:.2f}\n"
                f"🤝 COMPRA: ${buy:.2f}"
            )

        except:
            await update.message.reply_text("⚠️ Número inválido")


# =========================
# 🚀 MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🚀 BOT ACTIVO")
    app.run_polling()


if __name__ == "__main__":
    main()
