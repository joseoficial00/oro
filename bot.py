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
# 📋 MENÚ PRINCIPAL (2x2)
# =========================
async def main_menu(update: Update):

    keyboard = [
        ["🥇 CALCULAR VALOR 🥇", "📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵", "👑 PANEL ADMIN"]
    ]

    if not is_admin(update):
        keyboard[1][1] = " "

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
# 🏆 PUREZA
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
# 👑 PANEL ADMIN
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

    uid = update.effective_user.id

    if not is_authorized(update):
        await deny(update)
        return

    USER_NAMES[uid] = update.effective_user.first_name or "USER"

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

    dt = datetime.now(TZ_LOUISVILLE)
    fecha = dt.strftime("%d/%m/%Y")
    hora = dt.strftime("%I:%M:%S %p")


    # ================= BACK =================
    if text == "⬅️ VOLVER AL MENÚ":
        user_data.clear()
        await main_menu(update)
        return


    # ================= PANEL ADMIN =================
    if text == "👑 PANEL ADMIN":
        await admin_panel(update)
        user_data.clear()
        return


    # ================= VER USUARIOS =================
    if text == "📊 VER USUARIOS":
        msg = "👥 <b>USUARIOS</b>\n\n"
        for uid in AUTHORIZED_USERS:
            msg += f"{USER_NAMES.get(uid,'USER')} | ID: {uid} | Margen: {USER_MARGINS.get(uid,0.88)}\n"
        await update.message.reply_text(msg, parse_mode="HTML")
        return


    # ================= AGREGAR USUARIO =================
    if text == "➕ AGREGAR USUARIO":
        user_data["admin"] = "add_id"
        await update.message.reply_text("✍️ Envía ID del usuario")
        return

    if user_data.get("admin") == "add_id":
        user_data["temp_id"] = text
        user_data["admin"] = "add_name"
        await update.message.reply_text("✍️ Envía nombre del usuario")
        return

    if user_data.get("admin") == "add_name":
        try:
            uid = int(user_data["temp_id"])
            USER_NAMES[uid] = text
            USER_MARGINS[uid] = 0.88
            AUTHORIZED_USERS.add(uid)

            user_data.clear()
            await update.message.reply_text("✅ Usuario agregado")
        except:
            await update.message.reply_text("❌ Error")
        return


    # ================= EDITAR USUARIO =================
    if text == "✏️ EDITAR USUARIO":
        user_data["admin"] = "edit_select"

        kb = []
        for uid in AUTHORIZED_USERS:
            if uid == ADMIN_ID:
                continue
            kb.append([f"{USER_NAMES.get(uid,'USER')} | {uid}"])

        await update.message.reply_text(
            "👤 Selecciona usuario:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    if user_data.get("admin") == "edit_select":
        try:
            uid = int(text.split("|")[1].strip())
            user_data["edit_id"] = uid
            user_data["admin"] = "edit_menu"

            kb = [
                ["✏️ EDITAR NOMBRE", "💰 EDITAR MARGEN"],
                ["⬅️ VOLVER"]
            ]

            await update.message.reply_text(
                "¿Qué deseas editar?",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
            )
        except:
            await update.message.reply_text("❌ Error al seleccionar usuario")
        return


    if text == "✏️ EDITAR NOMBRE":
        user_data["admin"] = "edit_name"
        await update.message.reply_text("Envía nuevo nombre")
        return

    if text == "💰 EDITAR MARGEN":
        user_data["admin"] = "edit_margin"
        await update.message.reply_text("Envía nuevo margen (ej: 0.90)")
        return

    if user_data.get("admin") == "edit_name":
        USER_NAMES[user_data["edit_id"]] = text
        user_data.clear()
        await update.message.reply_text("✅ Nombre actualizado")
        return

    if user_data.get("admin") == "edit_margin":
        USER_MARGINS[user_data["edit_id"]] = float(text)
        user_data.clear()
        await update.message.reply_text("💰 Margen actualizado")
        return


    if text == "⬅️ VOLVER":
        user_data.clear()
        await admin_panel(update)
        return


    # ================= ELIMINAR USUARIO =================
    if text == "➖ QUITAR USUARIO":
        user_data["admin"] = "delete_select"

        kb = []
        for uid in AUTHORIZED_USERS:
            if uid != ADMIN_ID:
                kb.append([f"{USER_NAMES.get(uid,'USER')} | {uid}"])

        await update.message.reply_text(
            "Selecciona usuario a eliminar:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return


    if user_data.get("admin") == "delete_select":
        user_data["delete_id"] = int(text.split("|")[1].strip())
        user_data["admin"] = "delete_confirm"

        kb = [["SI", "NO"]]

        await update.message.reply_text(
            "⚠️ ¿Seguro que quieres eliminar este usuario?",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return


    if user_data.get("admin") == "delete_confirm":
        if text == "SI":
            uid = user_data["delete_id"]

            AUTHORIZED_USERS.discard(uid)
            USER_NAMES.pop(uid, None)
            USER_MARGINS.pop(uid, None)

            user_data.clear()

            await update.message.reply_text("❌ Usuario eliminado")
            await main_menu(update)
        else:
            user_data.clear()
            await admin_panel(update)
        return


    # ================= MENÚ =================
    if text == "🥇 CALCULAR VALOR 🥇":
        user_data["step"] = "select"
        await purity_menu(update)
        return


    # ================= PRECIO COMPRA =================
    if text == "💵 PRECIO DE COMPRA 💵":
        price = get_gold_price_ounce()
        if price:
            gram = price / 31.1035
            margin = USER_MARGINS.get(user_id, 0.88)

            await update.message.reply_text(
                f"💵 <b>PRECIO DE COMPRA POR GRAMO</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"🥇 10K: <code>${gram*GOLD_TYPES['10K']*margin:.2f}</code>\n"
                f"🥇 14K: <code>${gram*GOLD_TYPES['14K']*margin:.2f}</code>\n"
                f"🥇 18K: <code>${gram*GOLD_TYPES['18K']*margin:.2f}</code>\n"
                f"🥇 24K: <code>${gram*GOLD_TYPES['24K']*margin:.2f}</code>",
                parse_mode="HTML"
            )
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


    # ================= COTIZAR =================
    if user_data.get("step") == "select" and any(k in text for k in GOLD_TYPES):
        gold_type = next(k for k in GOLD_TYPES if k in text)
        user_data["gold_type"] = gold_type
        user_data["step"] = "grams"

        await update.message.reply_text(
            f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ Envíe los gramos:",
            parse_mode="HTML"
        )
        return


    if user_data.get("step") == "grams":
        try:
            grams = float(text.replace(",", "."))
            gold_type = user_data["gold_type"]

            price = get_gold_price_ounce()
            gram = price / 31.1035

            total = grams * gram * GOLD_TYPES[gold_type]
            buy = total * USER_MARGINS.get(user_id, 0.88)

            await update.message.reply_text(
                f"✨ <b>COTIZACIÓN</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"
                f"📦 <b>Quilate:</b> <code>{gold_type}</code>\n"
                f"⚖️ <b>Peso:</b> <code>{grams} g</code>\n\n"
                f"💰 <b>VALOR REAL:</b> <code>${total:,.2f} USD</code>\n"
                f"🤝 <b>PRECIO COMPRA (Neto):</b> <code>${buy:,.2f} USD</code>",
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
