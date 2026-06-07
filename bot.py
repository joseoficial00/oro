GOLD_TYPES = {
    "10K": 10 / 24,
    "14K": 14 / 24,
    "18K": 18 / 24,
    "24K": 1.0,
}

# ==========================================
# MENÚ PRINCIPAL
# ==========================================

async def main_menu(update: Update):
    keyboard = [
        ["🥇 CALCULAR VALOR 🥇"],
        ["📈 TASA EN TIEMPO REAL 💸"],
        ["💵 PRECIO DE COMPRA 💵"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    text = (
        "<b>💎 JCS GOLD CALCULATOR | PREMIUM 💎</b>\n\n"
        "✨ <b>Bienvenido al cotizador exclusivo.</b>\n"
        "» Conectado con los mercados globales.\n"
        "» Precisión matemática garantizada.\n\n"
        "👇 <i>Seleccione una opción:</i> 👇"
    )

    await update.effective_chat.send_message(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

# ==========================================
# MENÚ DE PUREZA
# ==========================================

async def purity_menu(update: Update):
    keyboard = [
        ["⚡ 10K", "⚡ 14K"],
        ["🌟 18K", "🏆 24K (Puro)"],
        ["⬅️ VOLVER AL MENÚ"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "<b>🏆 SELECCIÓN DE PUREZA</b>\n\nSeleccione el quilataje:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ==========================================
# HANDLE MESSAGES
# ==========================================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    dt_now = datetime.now(TZ_LOUISVILLE)
    fecha = dt_now.strftime("%d/%m/%Y")
    hora = dt_now.strftime("%I:%M:%S %p")

    # ======================================
    # PRECIO DE COMPRA
    # ======================================

    if text == "💵 PRECIO DE COMPRA 💵":

        price = get_gold_price_ounce()

        if price:

            gram_price_24k = price / 31.1035

            precio_10k = gram_price_24k * GOLD_TYPES["10K"] * 0.88
            precio_14k = gram_price_24k * GOLD_TYPES["14K"] * 0.88
            precio_18k = gram_price_24k * GOLD_TYPES["18K"] * 0.88
            precio_24k = gram_price_24k * GOLD_TYPES["24K"] * 0.88

            mensaje = (
                f"💵 <b>PRECIO DE COMPRA POR GRAMO</b>\n"
                f"📅 <code>{fecha}</code>\n"
                f"⏰ <code>{hora}</code>\n\n"

                f"🥇 <b>10K:</b> "
                f"<code>${precio_10k:.2f} USD/g</code>\n"

                f"🥇 <b>14K:</b> "
                f"<code>${precio_14k:.2f} USD/g</code>\n"

                f"🥇 <b>18K:</b> "
                f"<code>${precio_18k:.2f} USD/g</code>\n"

                f"🥇 <b>24K:</b> "
                f"<code>${precio_24k:.2f} USD/g</code>\n\n"

                f"📉 <i>Valores con descuento del 12% aplicado.</i>"
            )

            await update.message.reply_text(
                mensaje,
                parse_mode="HTML"
            )

        else:
            await update.message.reply_text(
                "❌ No se pudo obtener el precio actual del oro."
            )

    # ======================================
    # TASA EN TIEMPO REAL
    # ======================================

    elif text == "📈 TASA EN TIEMPO REAL 💸":

        price = get_gold_price_ounce()

        if price:

            msg = (
                f"📊 <b>TASA OFICIAL EN TIEMPO REAL</b>\n"
                f"⏱ <code>{fecha} {hora}</code>\n\n"
                f"🪙 <code>1 oz (Troy)</code> ➜ "
                f"<code>${price:,.2f} USD</code>\n"

                f"🥇 <code>1g Oro (24K)</code> ➜ "
                f"<code>${(price / 31.1035):,.2f} USD</code>\n"
            )

            await update.message.reply_text(
                msg,
                parse_mode="HTML"
            )

        else:
            await update.message.reply_text(
                "❌ No se pudo sincronizar la tasa actual."
            )

    # ======================================
    # CALCULAR VALOR
    # ======================================

    elif text == "🥇 CALCULAR VALOR 🥇":

        user_data["step"] = "select_purity"
        await purity_menu(update)

    elif text in ["⬅️ VOLVER", "⬅️ VOLVER AL MENÚ"]:

        user_data.clear()
        await main_menu(update)

    elif (
        user_data.get("step") == "select_purity"
        and any(q in text for q in GOLD_TYPES)
    ):

        gold_type = next(
            q for q in GOLD_TYPES
            if q in text
        )

        user_data["gold_type"] = gold_type
        user_data["step"] = "input_grams"

        await update.message.reply_text(
            f"👑 <b>QUILATAJE: {gold_type}</b>\n\n"
            f"✍️ Envíe la cantidad de gramos.\n\n"
            f"💡 Ejemplo: 12.5",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                [["⬅️ VOLVER"]],
                resize_keyboard=True
            )
        )

    elif user_data.get("step") == "input_grams":

        try:

            grams = float(text.replace(",", "."))
            gold_type = user_data["gold_type"]

            price = get_gold_price_ounce()

            if price:

                gram_price_24k = price / 31.1035

                gram_price_selected = (
                    gram_price_24k *
                    GOLD_TYPES[gold_type]
                )

                total_real = grams * gram_price_selected

                # DESCUENTO DEL 12%
                total_compra = total_real * 0.88

                resultado = (
                    f"✨ <b>COTIZACIÓN</b>\n"
                    f"📅 <code>{fecha}</code>\n"
                    f"⏰ <code>{hora}</code>\n\n"

                    f"📦 <b>Quilate:</b> "
                    f"<code>{gold_type}</code>\n"

                    f"⚖️ <b>Peso:</b> "
                    f"<code>{grams} g</code>\n\n"

                    f"💰 <b>VALOR REAL:</b>\n"
                    f"<code>${total_real:,.2f} USD</code>\n\n"

                    f"🤝 <b>PRECIO DE COMPRA:</b>\n"
                    f"<code>${total_compra:,.2f} USD</code>\n\n"

                    f"📉 <i>Descuento del 12% aplicado.</i>"
                )

                await update.message.reply_text(
                    resultado,
                    parse_mode="HTML"
                )

            else:
                await update.message.reply_text(
                    "❌ Error al obtener el precio del oro."
                )

        except ValueError:

            await update.message.reply_text(
                "⚠️ Introduzca un número válido.\nEjemplo: 10.5"
            )
