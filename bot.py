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

# 👑 ADMIN
ADMIN_ID = 6794562791

AUTHORIZED_USERS = {ADMIN_ID}

# usuarios registrados (ID -> info)
USERS = {}

# margen por usuario
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
# 👤 REGISTRO USUARIO
# =========================
def register_user(update: Update):
    user = update.effective_user
    USERS[user.id] = {
        "name": user.full_name,
        "username": user.username
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
# 📋 MENÚ PRINCIPAL
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 COTIZAR 🥇", "📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵", "⬅️ VOLVER AL MENÚ"]
    ]

    if is_admin(update):
        keyboard.append(["👑 PANEL ADMIN"])

    await update.effective_chat.send_message(
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Por favor, seleccione una acción del menú:</i> 👇",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 🏆 MENU PUREZA
# =========================
async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    await update.message.reply_text(
        "<b>🏆 SELECCIÓN DE PUREZA</b>\n\n"
        "Seleccione el quilataje del oro a evaluar:",
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
# 👑 PANEL ADMIN
# =========================
async def admin_panel(update: Update):
    if not is_admin(update):
        await deny(update)
        return

    keyboard = [
        ["📋 VER USUARIOS"],
        ["💰 CAMBIAR MARGEN"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    await update.message.reply_text(
        "👑 <b>PANEL ADMIN</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


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

    # ================= PANEL ADMIN =================
    if text == "👑 PANEL ADMIN":
        await admin_panel(update)
        return

    if text == "📋 VER USUARIOS" and is_admin(update):
        msg = "👥 <b>USUARIOS REGISTRADOS</b>\n\n"
        for uid, data in USERS.items():
            msg += f"• {data['name']} | ID: {uid}\n"
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    # ================= PRECIO COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if price:
            gram_price_24k = price / 31.1035

            msg = (
                f"💵 <b>PRECIO DE COMPRA POR GRAMO</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"🥇 <b>10K:</b> <code>${gram_price_24k * GOLD_TYPES['10K'] * margin:.2f}/g</code>\n"
                f"🥇 <b>14K:</b> <code>${gram_price_24k * GOLD_TYPES['14K'] * margin:.2f}/g</code>\n"
                f"🥇 <b>18K:</b> <code>${gram_price_24k * GOLD_TYPES['18K'] * margin:.2f}/g</code>\n"
                f"🥇 <b>24K:</b> <code>${gram_price_24k * GOLD_TYPES['24K'] * margin:.2f}/g</code>"
            )

            await update.message.reply_text(msg, parse_mode="HTML")
        return

    # ================= TASA =================
    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()

        if price:
            await update.message.reply_text(
                f"📊 <b>TASA OFICIAL EN TIEMPO REAL</b>\n"
                f"⏱ <code>{fecha} {hora}</code>\n\n"
                f"🪙 <code>1 oz (Troy)</code> ➜ <code>${price:,.2f} USD</code>\n"
                f"🥇 <code>1g Oro (24K)</code> ➜ <code>${(price / 31.1035):,.2f} USD</code>",
                parse_mode="HTML"
            )
        return

    # ================= COTIZAR =================
    if text == "🥇 COTIZAR 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)
        return

    # ================= VOLVER =================
    if text == "⬅️ VOLVER AL MENÚ":
        user_data.clear()
        await main_menu(update)
        return

    # ================= PUREZA =================
    if user_data.get("step") == "select_purity" and any(q in text for q in GOLD_TYPES):
        gold_type = next(q for q in GOLD_TYPES if q in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"

        await update.message.reply_text(
            f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ <b>Envíe la cantidad de gramos.</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["⬅️ VOLVER AL MENÚ"]], resize_keyboard=True)
        )
        return

    # ================= CÁLCULO =================
    if user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(",", "."))
            price = get_gold_price_ounce()

            if not price:
                return

            gram_price = price / 31.1035

            total_real = grams * gram_price * GOLD_TYPES[user_data["gold_type"]]
            total_compra = total_real * margin

            await update.message.reply_text(
                f"✨ <b>COTIZACIÓN</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"📦 <b>Quilate:</b> <code>{user_data['gold_type']}</code>\n"
                f"⚖️ <b>Peso:</b> <code>{grams} g</code>\n\n"
                f"💰 <b>VALOR REAL:</b> <code>${total_real:,.2f} USD</code>\n"
                f"🤝 <b>PRECIO COMPRA:</b> <code>${total_compra:,.2f} USD</code>",
                parse_mode="HTML"
            )

        except ValueError:
            await update.message.reply_text("⚠️ Número inválido")


# =========================
# 🚀 MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Bot iniciado correctamente...")
    app.run_polling()


if __name__ == "__main__":
    main()
