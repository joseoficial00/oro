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

# 👤 usuarios con info completa
USERS = {}

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
# 👤 REGISTRAR USUARIO
# =========================
def register_user(update: Update):
    u = update.effective_user
    USERS[u.id] = {
        "name": u.full_name,
        "username": u.username,
        "id": u.id
    }


# =========================
# 💰 API ORO
# =========================
def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return float(r.json()["price"])
        return None
    except:
        return None


# =========================
# 📋 MENÚ
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
        "✨ Bienvenido\n"
        "Selecciona una opción:",
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
# 👑 PANEL ADMIN
# =========================
async def admin_panel(update: Update):
    keyboard = [
        ["➕ AGREGAR USUARIO", "➖ QUITAR USUARIO"],
        ["💰 CAMBIAR MARGEN", "📊 VER USUARIOS"],
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

    register_user(update)

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
    user_data = context.user_data

    register_user(update)

    dt = datetime.now(TZ_LOUISVILLE)
    fecha = dt.strftime("%d/%m/%Y")
    hora = dt.strftime("%I:%M:%S %p")

    margin = USER_MARGINS.get(user_id, 0.88)

    # ================= ADMIN =================
    if text == "👑 PANEL ADMIN":
        await admin_panel(update)
        return

    # ➕ AGREGAR USUARIO
    if text == "➕ AGREGAR USUARIO":
        user_data["admin"] = "add"
        await update.message.reply_text("✍️ Envía ID del usuario")
        return

    # ➖ QUITAR
    if text == "➖ QUITAR USUARIO":
        user_data["admin"] = "remove"
        await update.message.reply_text("✍️ Envía ID del usuario")
        return

    # 💰 MARGEN
    if text == "💰 CAMBIAR MARGEN":
        user_data["admin"] = "margin"
        await update.message.reply_text("✍️ Envía: ID margen (ej: 123 0.90)")
        return

    # 📊 VER USUARIOS
    if text == "📊 VER USUARIOS":
        msg = "👥 <b>USUARIOS REGISTRADOS</b>\n\n"
        for uid, u in USERS.items():
            msg += f"{u['name']} (@{u['username']}) | ID: {uid}\n"
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    # ================= PROCESO ADMIN =================
    if is_admin(update):

        action = user_data.get("admin")

        if action == "add":
            try:
                uid = int(text)
                AUTHORIZED_USERS.add(uid)
                USER_MARGINS.setdefault(uid, 0.88)
                await update.message.reply_text(f"✅ Agregado {uid}")
            except:
                await update.message.reply_text("❌ Error")
            return

        if action == "remove":
            try:
                uid = int(text)
                AUTHORIZED_USERS.discard(uid)
                USERS.pop(uid, None)
                await update.message.reply_text(f"❌ Eliminado {uid}")
            except:
                await update.message.reply_text("❌ Error")
            return

        if action == "margin":
            try:
                uid, val = text.split()
                USER_MARGINS[int(uid)] = float(val)
                await update.message.reply_text("💰 Margen actualizado")
            except:
                await update.message.reply_text("❌ Formato: ID 0.90")
            return

    # ================= PRECIO COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":
        price = get_gold_price_ounce()
        if price:
            gram_price = price / 31.1035

            await update.message.reply_text(
                f"💵 <b>PRECIO POR GRAMO</b>\n"
                f"{fecha} {hora}\n\n"
                f"10K: ${gram_price * GOLD_TYPES['10K'] * margin:.2f}\n"
                f"14K: ${gram_price * GOLD_TYPES['14K'] * margin:.2f}\n"
                f"18K: ${gram_price * GOLD_TYPES['18K'] * margin:.2f}\n"
                f"24K: ${gram_price * GOLD_TYPES['24K'] * margin:.2f}",
                parse_mode="HTML"
            )
        return

    # ================= TASA =================
    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            await update.message.reply_text(
                f"📊 TASA\n{fecha} {hora}\n\n1oz ${price:,.2f}",
                parse_mode="HTML"
            )
        return

    # ================= COTIZAR =================
    if text == "🥇 COTIZAR 🥇":
        user_data["step"] = "select"
        await purity_menu(update)
        return

    # ================= VOLVER =================
    if text == "⬅️ VOLVER AL MENÚ":
        user_data.clear()
        await main_menu(update)
        return

    # ================= PUREZA =================
    if user_data.get("step") == "select" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "grams"

        await update.message.reply_text("Envía gramos:")
        return

    # ================= CALCULO =================
    if user_data.get("step") == "grams":
        try:
            grams = float(text.replace(",", "."))
            price = get_gold_price_ounce()

            gram_price = price / 31.1035

            total = grams * gram_price * GOLD_TYPES[user_data["gold_type"]]
            buy = total * margin

            await update.message.reply_text(
                f"✨ COTIZACIÓN\n"
                f"{fecha} {hora}\n\n"
                f"{grams}g {user_data['gold_type']}\n\n"
                f"REAL: ${total:,.2f}\n"
                f"COMPRA: ${buy:,.2f}"
            )

        except:
            await update.message.reply_text("❌ Error")


# =========================
# 🚀 MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("BOT ACTIVO")
    app.run_polling()


if __name__ == "__main__":
    main()
