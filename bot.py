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
# 📋 MENÚ 2x2 (ORIGINAL)
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
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Por favor, seleccione una acción del menú:</i> 👇",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# 🏆 PUREZA (ORIGINAL)
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
# 👑 ADMIN PANEL
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
# 🗑 LISTA ELIMINAR
# =========================
async def delete_menu(update: Update):

    keyboard = []
    for uid in AUTHORIZED_USERS:
        if uid != ADMIN_ID:
            keyboard.append([f"{USER_NAMES.get(uid,'USER')} | {uid}"])

    keyboard.append(["⬅️ VOLVER"])

    await update.message.reply_text(
        "➖ <b>SELECCIONA USUARIO A ELIMINAR</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# =========================
# ⚠️ CONFIRMACIÓN
# =========================
async def confirm_delete(update: Update, uid: int):

    await update.message.reply_text(
        f"⚠️ <b>¿Seguro que quieres eliminar al usuario {uid}?</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ SÍ ELIMINAR", "❌ CANCELAR"]],
            resize_keyboard=True
        )
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


    # ================= ADMIN =================
    if text == "👑 PANEL ADMIN":
        await admin_panel(update)
        data.clear()
        return

    if text == "⬅️ VOLVER AL MENÚ":
        data.clear()
        await main_menu(update)
        return


    # ================= ADMIN ACTIONS =================
    if is_admin(update):

        if text == "➕ AGREGAR USUARIO":
            data["admin"] = "add"
            await update.message.reply_text("✍️ Envía: ID NOMBRE MARGEN")
            return

        if text == "➖ QUITAR USUARIO":
            data["admin"] = "select_delete"
            await delete_menu(update)
            return

        if text == "✏️ EDITAR USUARIO":
            data["admin"] = "edit_menu"
            await update.message.reply_text(
                "✏️ EDITAR USUARIO\n1️⃣ Nombre\n2️⃣ Margen",
                reply_markup=ReplyKeyboardMarkup(
                    [["✏️ EDITAR NOMBRE", "💰 EDITAR MARGEN"], ["⬅️ VOLVER"]],
                    resize_keyboard=True
                )
            )
            return

        if text == "📊 VER USUARIOS":
            msg = "👥 <b>USUARIOS</b>\n\n"
            for uid in AUTHORIZED_USERS:
                msg += f"{USER_NAMES.get(uid)} | {uid} | {USER_MARGINS.get(uid,0.88)}\n"
            await update.message.reply_text(msg, parse_mode="HTML")
            return


        # ================= ADD =================
        if data.get("admin") == "add":
            try:
                uid, name, margin = text.split()
                AUTHORIZED_USERS.add(int(uid))
                USER_NAMES[int(uid)] = name
                USER_MARGINS[int(uid)] = float(margin)
                data.clear()
                await update.message.reply_text("✅ Usuario agregado")
            except:
                await update.message.reply_text("❌ ID NOMBRE MARGEN")
            return


        # ================= DELETE FLOW =================
        if data.get("admin") == "select_delete":

            if text == "⬅️ VOLVER":
                data.clear()
                await admin_panel(update)
                return

            try:
                uid = int(text.split("|")[-1])
                data["delete_id"] = uid
                data["admin"] = "confirm_delete"
                await confirm_delete(update, uid)
            except:
                await update.message.reply_text("❌ Selección inválida")
            return


        if data.get("admin") == "confirm_delete":

            uid = data.get("delete_id")

            if text == "✅ SÍ ELIMINAR":
                AUTHORIZED_USERS.discard(uid)
                USER_NAMES.pop(uid, None)
                USER_MARGINS.pop(uid, None)
                data.clear()
                await update.message.reply_text("❌ Usuario eliminado")
                return

            if text == "❌ CANCELAR":
                data.clear()
                await admin_panel(update)
                return


    # ================= MENÚ PRINCIPAL =================
    if text == "🥇 COTIZAR 🥇":
        data["step"] = "select"
        await purity_menu(update)
        return


    # ================= PRECIO COMPRA (ORIGINAL) =================
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


    # ================= TASA (ORIGINAL) =================
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


    # ================= PUREZA + CALCULO (ORIGINAL) =================
    if data.get("step") == "select" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        data["gold_type"] = gold_type
        data["step"] = "grams"

        await update.message.reply_text(
f"""👑 <b>QUILATAJE: {gold_type}</b>

✍️ <b>Envíe la cantidad de gramos en formato numérico.</b>

💡 <i>Ejemplos: 10 o 5.75</i>""",
            parse_mode="HTML"
        )
        return


    if data.get("step") == "grams":
        try:
            grams = float(text.replace(",", "."))
            gold_type = data["gold_type"]

            price = get_gold_price_ounce()
            if not price:
                return

            gram = price / 31.1035
            total = grams * gram * GOLD_TYPES[gold_type]
            buy = total * USER_MARGINS.get(user_id, 0.88)

            await update.message.reply_text(
f"""✨ <b>COTIZACIÓN</b>

📅 <code>{fecha}</code>
⏰ <code>{hora}</code>

📦 <b>Quilate:</b> <code>{gold_type}</code>
⚖️ <b>Peso:</b> <code>{grams} g</code>

💰 <b>VALOR REAL:</b> <code>${total:,.2f} USD</code>
🤝 <b>PRECIO COMPRA (Neto):</b> <code>${buy:,.2f} USD</code>

✍️ <i>Envíe otro peso o Volver</i>""",
                parse_mode="HTML"
            )

        except:
            await update.message.reply_text("⚠️ Número inválido")


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
