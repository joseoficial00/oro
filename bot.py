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

# 👑 TU ID DE ADMIN
ADMIN_ID = 6794562791

# Usuarios autorizados
AUTHORIZED_USERS = {ADMIN_ID}

# Márgenes por usuario (default 0.88)
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
# 🔐 SEGURIDAD
# =========================
def is_authorized(update: Update):
    return update.effective_user.id in AUTHORIZED_USERS


def is_admin(update: Update):
    return update.effective_user.id == ADMIN_ID


async def access_denied(update: Update):
    await update.effective_chat.send_message(
        "⛔ ACCESO DENEGADO"
    )


# =========================
# 🌟 API ORO
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
    except Exception:
        return None


# =========================
# 📋 MENÚ
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵"],
    ]

    if is_admin(update):
        keyboard.append(["👑 PANEL ADMIN"])

    await update.effective_chat.send_message(
        "<b>💎 GOLD BOT PRO 💎</b>\nSeleccione una opción:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K"],
        ["🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    await update.message.reply_text(
        "Seleccione quilataje:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 👑 PANEL ADMIN
# =========================
async def admin_panel(update: Update):
    if not is_admin(update):
        await access_denied(update)
        return

    keyboard = [
        ["➕ AGREGAR USUARIO"],
        ["➖ ELIMINAR USUARIO"],
        ["💰 CAMBIAR MARGEN"],
        ["📋 VER USUARIOS"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    await update.message.reply_text(
        "👑 PANEL ADMIN",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 🚀 START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await access_denied(update)
        return

    context.user_data.clear()
    await main_menu(update)


# =========================
# 💬 MENSAJES
# =========================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_authorized(update):
        await access_denied(update)
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

    if text == "📋 VER USUARIOS":
        if not is_admin(update):
            return

        msg = "📋 USUARIOS:\n\n"
        for uid in AUTHORIZED_USERS:
            margin = USER_MARGINS.get(uid, 0.88)
            msg += f"👤 {uid} | Margen: {margin}\n"

        await update.message.reply_text(msg)
        return

    if text == "➕ AGREGAR USUARIO":
        if not is_admin(update):
            return

        user_data["step"] = "add_user"
        await update.message.reply_text("Envíe ID del usuario:")
        return

    if text == "➖ ELIMINAR USUARIO":
        if not is_admin(update):
            return

        user_data["step"] = "del_user"
        await update.message.reply_text("Envíe ID a eliminar:")
        return

    if text == "💰 CAMBIAR MARGEN":
        if not is_admin(update):
            return

        user_data["step"] = "set_margin"
        await update.message.reply_text("Formato: ID 90 (ej: 222222222 88)")
        return

    # ================= ADMIN INPUT =================
    if user_data.get("step") == "add_user":
        try:
            uid = int(text)
            AUTHORIZED_USERS.add(uid)
            USER_MARGINS[uid] = 0.88
            user_data.clear()
            await update.message.reply_text("✅ Usuario agregado")
        except:
            await update.message.reply_text("❌ ID inválido")
        return

    if user_data.get("step") == "del_user":
        try:
            uid = int(text)
            AUTHORIZED_USERS.discard(uid)
            USER_MARGINS.pop(uid, None)
            user_data.clear()
            await update.message.reply_text("🗑 Usuario eliminado")
        except:
            await update.message.reply_text("❌ Error")
        return

    if user_data.get("step") == "set_margin":
        try:
            uid, margin = text.split()
            uid = int(uid)
            margin = float(margin) / 100

            USER_MARGINS[uid] = margin
            AUTHORIZED_USERS.add(uid)

            user_data.clear()
            await update.message.reply_text(f"✅ Margen actualizado: {margin}")
        except:
            await update.message.reply_text("❌ Formato: ID 90")
        return

    # ================= MENÚ NORMAL =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if price:
            gram = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

            msg = (
                f"💵 PRECIO COMPRA\n\n"
                f"🥇 10K: ${gram * GOLD_TYPES['10K'] * margin:.2f}/g\n"
                f"🥇 14K: ${gram * GOLD_TYPES['14K'] * margin:.2f}/g\n"
                f"🥇 18K: ${gram * GOLD_TYPES['18K'] * margin:.2f}/g\n"
                f"🥇 24K: ${gram * GOLD_TYPES['24K'] * margin:.2f}/g"
            )

            await update.message.reply_text(msg)

        return

    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()

        if price:
            await update.message.reply_text(
                f"📊 1 oz: ${price:,.2f}\n"
                f"🥇 1g: ${(price / 31.1035):,.2f}"
            )
        return

    if text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)
        return

    if text in ["⬅️ VOLVER AL MENÚ"]:
        user_data.clear()
        await main_menu(update)
        return

    # ================= PUREZA =================
    if user_data.get("step") == "select_purity" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"

        await update.message.reply_text("Envíe gramos:")
        return

    # ================= CALCULAR =================
    if user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(",", "."))
            gold_type = user_data["gold_type"]

            price = get_gold_price_ounce()
            if not price:
                return

            gram = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

            value = grams * gram * GOLD_TYPES[gold_type]
            buy = value * margin

            await update.message.reply_text(
                f"✨ RESULTADO\n\n"
                f"{gold_type} | {grams}g\n"
                f"💰 Valor: ${value:.2f}\n"
                f"🤝 Compra: ${buy:.2f}"
            )
        except:
            await update.message.reply_text("Número inválido")


# =========================
# 🚀 MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Bot activo...")
    app.run_polling()


if __name__ == "__main__":
    main()
