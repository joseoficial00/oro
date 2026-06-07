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
# 📋 MENÚ
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 COTIZAR 🥇", "📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵", "👑 PANEL ADMIN"]
    ]

    if not is_admin(update):
        keyboard[1][1] = "⛔"

    await update.effective_chat.send_message(
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "👇 Selecciona una opción 👇",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


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
# 👑 ADMIN PANEL
# =========================
async def admin_panel(update: Update):
    keyboard = [
        ["➕ AGREGAR USUARIO", "➖ QUITAR USUARIO"],
        ["📊 VER USUARIOS", "⬅️ VOLVER AL MENÚ"]
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

    # ================= ADMIN PANEL =================
    if text == "👑 PANEL ADMIN":
        await admin_panel(update)
        return

    if text == "⬅️ VOLVER AL MENÚ":
        data.clear()
        await main_menu(update)
        return


    # ================= ADMIN FLOW PRO =================
    if is_admin(update):

        # paso 1
        if text == "➕ AGREGAR USUARIO":
            data["step"] = "add_id"
            await update.message.reply_text("✍️ Envía ID del usuario")
            return

        # paso 2
        if data.get("step") == "add_id":
            data["new_id"] = int(text)
            data["step"] = "add_name"
            await update.message.reply_text("✍️ Envía nombre del usuario")
            return

        # paso 3
        if data.get("step") == "add_name":
            uid = data["new_id"]
            name = text

            USER_NAMES[uid] = name
            AUTHORIZED_USERS.add(uid)

            data["step"] = "add_margin"
            await update.message.reply_text("✍️ Envía margen (ej: 0.88)")
            return

        # paso 4
        if data.get("step") == "add_margin":
            uid = data["new_id"]
            USER_MARGINS[uid] = float(text)

            data.clear()
            await update.message.reply_text("✅ Usuario creado completo")
            return

        # quitar usuario
        if text == "➖ QUITAR USUARIO":
            data["step"] = "remove"
            await update.message.reply_text("✍️ Envía ID del usuario")
            return

        if data.get("step") == "remove":
            uid = int(text)
            AUTHORIZED_USERS.discard(uid)
            USER_NAMES.pop(uid, None)
            USER_MARGINS.pop(uid, None)
            data.clear()
            await update.message.reply_text("❌ Usuario eliminado")
            return

        # ver usuarios
        if text == "📊 VER USUARIOS":
            msg = "👥 <b>USUARIOS</b>\n\n"
            for uid in AUTHORIZED_USERS:
                msg += f"{USER_NAMES.get(uid,'USER')} | ID:{uid} | Margen:{USER_MARGINS.get(uid,0.88)}\n"
            await update.message.reply_text(msg, parse_mode="HTML")
            return


    # ================= COTIZAR =================
    if text == "🥇 COTIZAR 🥇":
        data["step"] = "select"
        await purity_menu(update)
        return


    # ================= COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":
        price = get_gold_price_ounce()
        if price:
            gram = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

            msg = (
f"""💵 <b>PRECIO DE COMPRA</b>

📅 {fecha}
⏰ {hora}

🥇 10K: ${gram*GOLD_TYPES['10K']*margin:.2f}
🥇 14K: ${gram*GOLD_TYPES['14K']*margin:.2f}
🥇 18K: ${gram*GOLD_TYPES['18K']*margin:.2f}
🥇 24K: ${gram*GOLD_TYPES['24K']*margin:.2f}"""
            )

            await update.message.reply_text(msg, parse_mode="HTML")
        return


    # ================= TASA =================
    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            await update.message.reply_text(
                f"📊 TASA\n🪙 1 oz: ${price:,.2f}\n🥇 1g: ${(price/31.1035):,.2f}",
                parse_mode="HTML"
            )
        return


# =========================
# 🚀 RUN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🚀 BOT PRO ACTIVO")
    app.run_polling()


if __name__ == "__main__":
    main()
