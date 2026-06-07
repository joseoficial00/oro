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

# 👑 TU ID (ADMIN)
ADMIN_ID = 6794562791

# Usuarios autorizados
AUTHORIZED_USERS = {ADMIN_ID}

# Margen por usuario
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
# 🔐 CONTROL DE ACCESO
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
    headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return float(r.json()["price"])
        return None
    except:
        return None


# =========================
# 📋 MENÚ (NO TOCADO)
# =========================
async def main_menu(update: Update):
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵"]
    ]

    if is_admin(update):
        keyboard.append(["👑 PANEL ADMIN"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = (
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Por favor, seleccione una acción del menú:</i> 👇"
    )

    await update.effective_chat.send_message(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K"],
        ["🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = (
        "<b>🏆 SELECCIÓN DE PUREZA</b>\n\n"
        "Seleccione el quilataje del oro a evaluar:"
    )

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


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
    user_data = context.user_data

    dt_now = datetime.now(TZ_LOUISVILLE)
    fecha = dt_now.strftime("%d/%m/%Y")
    hora = dt_now.strftime("%I:%M:%S %p")

    # ================= ADMIN PANEL =================
    if text == "👑 PANEL ADMIN" and is_admin(update):
        await update.message.reply_text(
            "👑 PANEL ADMIN\n\n"
            "➕ AGREGAR USUARIO\n"
            "➖ ELIMINAR USUARIO\n"
            "💰 CAMBIAR MARGEN\n"
            "📋 VER USUARIOS"
        )
        return

    if text == "📋 VER USUARIOS" and is_admin(update):
        msg = "📋 USUARIOS:\n\n"
        for uid in AUTHORIZED_USERS:
            msg += f"👤 {uid} | Margen: {USER_MARGINS.get(uid, 0.88)}\n"
        await update.message.reply_text(msg)
        return

    if text == "➕ AGREGAR USUARIO" and is_admin(update):
        user_data["step"] = "add_user"
        await update.message.reply_text("Envíe ID del usuario")
        return

    if text == "➖ ELIMINAR USUARIO" and is_admin(update):
        user_data["step"] = "del_user"
        await update.message.reply_text("Envíe ID a eliminar")
        return

    if text == "💰 CAMBIAR MARGEN" and is_admin(update):
        user_data["step"] = "set_margin"
        await update.message.reply_text("Formato: ID 90")
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
            await update.message.reply_text("❌ Error")
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
            USER_MARGINS[uid] = float(margin) / 100
            AUTHORIZED_USERS.add(uid)
            user_data.clear()
            await update.message.reply_text("✅ Margen actualizado")
        except:
            await update.message.reply_text("❌ Formato: ID 90")
        return

    # ================= PRECIO COMPRA (MISMO TEXTO TUYO) =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if price:
            gram_price_24k = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

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

    # ================= RESTO ORIGINAL SIN CAMBIOS =================
    if text == "📈 TASA EN TIEMPO REAL 💸":
        price = get_gold_price_ounce()
        if price:
            msg = (
                f"📊 <b>TASA OFICIAL EN TIEMPO REAL</b>\n"
                f"⏱ <code>{fecha} {hora}</code>\n\n"
                f"🪙 <code>1 oz (Troy)</code> ➜ <code>${price:,.2f} USD</code>\n"
                f"🥇 <code>1g Oro (24K)</code> ➜ <code>${(price / 31.1035):,.2f} USD</code>"
            )
            await update.message.reply_text(msg, parse_mode="HTML")
        return

    if text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select_purity"
        await purity_menu(update)

    elif text in ["⬅️ VOLVER AL MENÚ", "⬅️ VOLVER"]:
        user_data.clear()
        await main_menu(update)

    elif user_data.get("step") == "select_purity" and any(q in text for q in GOLD_TYPES):
        gold_type = next(q for q in GOLD_TYPES if q in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"

        await update.message.reply_text(
            f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ <b>Envíe la cantidad de gramos en formato numérico.</b>\n\n"
            f"💡 <i>Ejemplos: 10 o 5.75</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([["⬅️ VOLVER"]], resize_keyboard=True)
        )

    elif user_data.get("step") == "input_grams":
        try:
            grams = float(text.replace(',', '.'))
            gold_type = user_data["gold_type"]
            price = get_gold_price_ounce()

            if price:
                gram_price_24k = price / 31.1035
                gram_price_selected = gram_price_24k * GOLD_TYPES[gold_type]

                total_real = grams * gram_price_selected
                total_compra = total_real * USER_MARGINS.get(user_id, 0.88)

                res = (
                    f"✨ <b>COTIZACIÓN</b>\n"
                    f"📅 <code>{fecha}</code>\n"
                    f"⏰ <code>{hora}</code>\n\n"
                    f"📦 <b>Quilate:</b> <code>{gold_type}</code>\n"
                    f"⚖️ <b>Peso:</b> <code>{grams} g</code>\n\n"
                    f"💰 <b>VALOR REAL:</b> <code>${total_real:,.2f} USD</code>\n"
                    f"🤝 <b>PRECIO COMPRA:</b> <code>${total_compra:,.2f} USD</code>\n\n"
                    f"✍️ <i>Envíe otro peso o presione Volver.</i>"
                )

                await update.message.reply_text(res, parse_mode="HTML")

        except ValueError:
            await update.message.reply_text("⚠️ Por favor, envíe un número válido")
