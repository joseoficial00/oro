import logging
import requests
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# 🔑 LOAD ENV (.env)
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOLD_API_KEY = os.getenv("GOLD_API_KEY")

# =========================
# 👑 CONFIG
# =========================
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
# 💰 GOLD API
# =========================
def get_gold_price_ounce():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {
        "x-access-token": GOLD_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        return float(data.get("price"))
    except:
        return None


# =========================
# 📋 MENÚ PRINCIPAL 2x2
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
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Por favor, seleccione una acción del menú:</i> 👇",
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
        ["➕ AGREGAR USUARIO", "📊 VER USUARIOS"],
        ["➖ QUITAR USUARIO", "💰 CAMBIAR MARGEN"],
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

    uid = update.effective_user.id

    if not is_authorized(update):
        await deny(update)
        return

    USER_NAMES[uid] = update.effective_user.first_name or "USER"

    context.user_data.clear()
    await main_menu(update)


# =========================
# 💬 HANDLE MESSAGES
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
            data["step"] = "add_id"
            await update.message.reply_text("✍️ Envía ID del usuario")
            return

        if text == "📊 VER USUARIOS":
            msg = "👥 <b>USUARIOS</b>\n\n"
            for uid in AUTHORIZED_USERS:
                msg += f"👤 {USER_NAMES.get(uid,'USER')} | ID: {uid} | Margen: {USER_MARGINS.get(uid,0.88)}\n"
            await update.message.reply_text(msg, parse_mode="HTML")
            return

        if text == "➖ QUITAR USUARIO":
            data["step"] = "remove_id"
            await update.message.reply_text("✍️ Envía ID a eliminar")
            return

        if text == "💰 CAMBIAR MARGEN":
            data["step"] = "margin"
            await update.message.reply_text("✍️ Envía: ID y margen (ej: 123 0.90)")
            return

        # ADD FLOW
        if data.get("step") == "add_id":
            data["new_id"] = int(text)
            data["step"] = "add_name"
            await update.message.reply_text("✍️ Envía el nombre")
            return

        if data.get("step") == "add_name":
            uid = data["new_id"]
            USER_NAMES[uid] = text
            AUTHORIZED_USERS.add(uid)
            data["step"] = "add_margin"
            await update.message.reply_text("💰 Envía margen")
            return

        if data.get("step") == "add_margin":
            uid = data["new_id"]
            USER_MARGINS[uid] = float(text)
            data.clear()
            await update.message.reply_text("✅ Usuario agregado")
            return

        # REMOVE FLOW
        if data.get("step") == "remove_id":
            try:
                uid = int(text)
                AUTHORIZED_USERS.discard(uid)
                USER_NAMES.pop(uid, None)
                USER_MARGINS.pop(uid, None)
                data.clear()
                await update.message.reply_text("❌ Usuario eliminado")
                await main_menu(update)
            except:
                await update.message.reply_text("❌ ID inválido")
            return

        # MARGIN
        if data.get("step") == "margin":
            try:
                uid, val = text.split()
                USER_MARGINS[int(uid)] = float(val)
                data.clear()
                await update.message.reply_text("💰 Margen actualizado")
            except:
                await update.message.reply_text("❌ Formato: ID 0.90")
            return


    # ================= PRECIO COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()
        if not price:
            await update.message.reply_text("⚠️ Error API")
            return

        gram = price / 31.1035
        margin = USER_MARGINS.get(user_id, 0.88)

        msg = (
f"""💵 <b>PRECIO DE COMPRA POR GRAMO</b>

📅 <code>{fecha}</code>
⏰ <code>{hora}</code>

🥇 10K: <code>${gram*GOLD_TYPES['10K']*margin:.2f}</code>
🥇 14K: <code>${gram*GOLD_TYPES['14K']*margin:.2f}</code>
🥇 18K: <code>${gram*GOLD_TYPES['18K']*margin:.2f}</code>
🥇 24K: <code>${gram*GOLD_TYPES['24K']*margin:.2f}</code>"""
        )

        await update.message.reply_text(msg, parse_mode="HTML")
        return


    # ================= TASA =================
    if text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()
        if not price:
            await update.message.reply_text("⚠️ Error API")
            return

        gram = price / 31.1035

        await update.message.reply_text(
f"""📊 <b>TASA EN TIEMPO REAL</b>

⏱ {fecha} {hora}

🪙 1 oz → ${price:,.2f}
🥇 1g → ${gram:,.2f}""",
            parse_mode="HTML"
        )
        return


    # ================= COTIZAR =================
    if text == "🥇 COTIZAR 🥇":
        data["step"] = "select"
        await purity_menu(update)
        return


    # ================= PUREZA =================
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


    # ================= CALCULO =================
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
