import logging
import requests
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURACION
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8723973833:AAFmyX4SK3DTE15fFUKu5AiofRS3QaQ2AA4")
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "goldapi-4ggdsmjfphsjl-io")

GOLD_TYPES = {"10K": 10/24, "14K": 14/24, "18K": 18/24, "22K": 22/24, "24K": 1.0}

def get_gold_price():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return float(r.json()["price"]) if r.status_code == 200 else None
    except: return None

# =========================
# MENÚS
# =========================

async def main_menu(update: Update):
    keyboard = [["🥇 CALCULAR"], ["📈 TASA REAL"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.effective_chat.send_message("✨ *JCS GOLD*\nSeleccione una opción:", reply_markup=reply_markup, parse_mode="Markdown")

async def purity_menu(update: Update):
    keyboard = [["10K", "14K"], ["18K", "22K"], ["24K"], ["⬅️ VOLVER"]]
    await update.message.reply_text("💎 *QUILATAJE:*", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), parse_mode="Markdown")

# =========================
# HANDLERS
# =========================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if text == "📈 TASA REAL":
        price = get_gold_price()
        if price:
            await update.message.reply_text(f"📊 *XAU/USD*\nOz: `${price:,.2f}`\nGramo 24K: `${(price/31.1035):,.2f}`", parse_mode="Markdown")

    elif text == "🥇 CALCULAR":
        user_data["step"] = "purity"
        await purity_menu(update)

    elif text == "⬅️ VOLVER":
        user_data.clear()
        await main_menu(update)

    elif text in GOLD_TYPES and user_data.get("step") == "purity":
        user_data.update({"type": text, "step": "grams"})
        await update.message.reply_text(f"✅ *{text}*\nEnvíe los gramos:", parse_mode="Markdown")

    elif user_data.get("step") == "grams":
        try:
            grams = float(text.replace(',', '.'))
            price = get_gold_price()
            if price:
                # Cálculo real y cálculo con -10%
                real_gram = (price / 31.1035) * GOLD_TYPES[user_data["type"]]
                total_real = grams * real_gram
                total_compra = total_real * 0.90 # Aplicando el 10% de ganancia para ti

                res = (
                    f"🏆 *RESULTADO: {user_data['type']}*\n"
                    f"Peso: `{grams}g`\n\n"
                    f"💰 *VALOR REAL:* `${total_real:,.2f}`\n"
                    f"🤝 *PRECIO COMPRA:* `${total_compra:,.2f}`\n\n"
                    f"✍️ _Envíe otro peso o presione Volver._"
                )
                await update.message.reply_text(res, parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Número inválido.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == "__main__":
    main()
