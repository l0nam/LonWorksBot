import logging
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
    ContextTypes
)
from datetime import datetime

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Состояния диалога ────────────────────────────────────────────
(
    CHOOSE_TYPE,
    ENTER_TITLE,
    ENTER_TZ,
    ENTER_BUDGET,
    ENTER_DEADLINE,
    ENTER_CONTACTS,
    CONFIRM,
    WAITING_REPLY,
) = range(8)

# ─── Конфиг из переменных среды ──────────────────────────────────
BOT_TOKEN   = os.environ["BOT_TOKEN"]
ADMIN_ID    = int(os.environ["ADMIN_ID"])   # твой Telegram user ID

SERVICE_LABELS = {
    "denizen":  "🧩 Denizen Script плагин",
    "website":  "🌐 Сайт",
    "design":   "🎨 Дизайн",
    "other":    "💡 Другое",
}

# ─── /start ───────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton(label, callback_data=key)]
        for key, label in SERVICE_LABELS.items()
    ]
    await update.message.reply_text(
        "👋 *Привет!* Я принимаю заказы на:\n\n"
        "🧩 *Denizen Script* — плагины для Minecraft\n"
        "🌐 *Сайты* — лендинги, веб‑приложения\n"
        "🎨 *Дизайн* — UI/UX, графика, брендинг\n\n"
        "Выбери тип работы 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return CHOOSE_TYPE


# ─── Шаг 1: тип работы ───────────────────────────────────────────
async def choose_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["service_type"] = query.data
    await query.edit_message_text(
        f"Отлично, выбрано: *{SERVICE_LABELS[query.data]}*\n\n"
        "✏️ Напиши *суть* проекта в двух словах (одностаничка для магазина, скрипт на мяч):",
        parse_mode="Markdown",
    )
    return ENTER_TITLE


# ─── Шаг 2: название ─────────────────────────────────────────────
async def enter_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(
        "📋 Теперь напиши подробное *техническое задание*.\n\n"
        "_Чем детальнее — тем точнее будет оценка._\n\n"
        "Желательно включить:\n"
        "• Функционал / страницы / экраны\n"
        "• Референсы (ссылки, примеры)\n"
        "• Технические требования\n"
        "• Любые важные детали",
        parse_mode="Markdown",
    )
    return ENTER_TZ


# ─── Шаг 3: ТЗ ───────────────────────────────────────────────────
async def enter_tz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["tz"] = update.message.text.strip()
    await update.message.reply_text(
        "💰 Укажи *бюджет* (или напиши «не знаю»):",
        parse_mode="Markdown",
    )
    return ENTER_BUDGET


# ─── Шаг 4: бюджет ───────────────────────────────────────────────
async def enter_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["budget"] = update.message.text.strip()
    await update.message.reply_text(
        "📅 Укажи *дедлайн* — когда нужно готово? (или «не горит»):",
        parse_mode="Markdown",
    )
    return ENTER_DEADLINE


# ─── Шаг 5: дедлайн ──────────────────────────────────────────────
async def enter_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["deadline"] = update.message.text.strip()
    await update.message.reply_text(
        "📞 Укажи *контакт* для связи:\n"
        "Telegram (@username), email или другой мессенджер:",
        parse_mode="Markdown",
    )
    return ENTER_CONTACTS


# ─── Шаг 6: контакты ─────────────────────────────────────────────
async def enter_contacts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["contacts"] = update.message.text.strip()
    d = ctx.user_data
    preview = (
        f"📦 *Проверь заказ перед отправкой:*\n\n"
        f"🔹 *Тип:* {SERVICE_LABELS[d['service_type']]}\n"
        f"🔹 *Название:* {d['title']}\n"
        f"🔹 *Бюджет:* {d['budget']}\n"
        f"🔹 *Дедлайн:* {d['deadline']}\n"
        f"🔹 *Контакт:* {d['contacts']}\n\n"
        f"📋 *ТЗ:*\n{d['tz']}\n\n"
        "Всё верно?"
    )
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Отправить", callback_data="confirm_yes"),
            InlineKeyboardButton("✏️ Начать заново", callback_data="confirm_no"),
        ]
    ])
    await update.message.reply_text(preview, parse_mode="Markdown", reply_markup=kb)
    return CONFIRM


# ─── Шаг 7: подтверждение ────────────────────────────────────────
async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        try:
            await query.edit_message_text("Хорошо, начнём заново. Введи /start")
        except Exception:
            await query.message.reply_text("Хорошо, начнём заново. Введи /start")
        return ConversationHandler.END

    d = ctx.user_data
    user = update.effective_user
    now  = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Сообщение клиенту — сразу редактируем, пока не слали запрос админу
    success_text = (
        "✅ *Заказ отправлен!*\n\n"
        "Мы получили вашу заявку и свяжемся с вами в ближайшее время.\n"
        "Обычно отвечаем в течение нескольких часов 🕐\n\n"
        "Хотите оформить ещё один заказ? → /start"
    )
    try:
        await query.edit_message_text(success_text, parse_mode="Markdown")
    except Exception:
        await query.message.reply_text(success_text, parse_mode="Markdown")

    # Сообщение администратору
    tz_preview = d['tz'] if len(d['tz']) <= 3000 else d['tz'][:3000] + "\n\n_[...текст обрезан, полное ТЗ выше]_"
    admin_text = (
        f"🔔 *НОВЫЙ ЗАКАЗ* [{now}]\n\n"
        f"👤 *От:* [{user.full_name}](tg://user?id={user.id})\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"📱 *Username:* @{user.username or '—'}\n\n"
        f"🔹 *Тип:* {SERVICE_LABELS[d['service_type']]}\n"
        f"🔹 *Название:* {d['title']}\n"
        f"🔹 *Бюджет:* {d['budget']}\n"
        f"🔹 *Дедлайн:* {d['deadline']}\n"
        f"🔹 *Контакт клиента:* {d['contacts']}\n\n"
        f"📋 *ТЗ:*\n{tz_preview}"
    )
    kb_admin = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Ответить через бота",
                callback_data=f"reply_{user.id}",
            ),
            InlineKeyboardButton(
                "👤 Написать напрямую",
                url=f"tg://user?id={user.id}",
            ),
        ]
    ])
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            admin_text,
            parse_mode="Markdown",
            reply_markup=kb_admin,
        )
    except Exception as e:
        logger.error(f"Не удалось отправить заказ админу: {e}")

    return ConversationHandler.END


# ─── Кнопка «Ответить через бота» у админа ───────────────────────
async def admin_reply_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target_id = int(query.data.split("_")[1])
    ctx.user_data["reply_to"] = target_id
    await query.message.reply_text(
        f"✏️ Напиши ответ клиенту (ID: `{target_id}`).\n"
        "Отправь сообщение прямо сюда:",
        parse_mode="Markdown",
    )
    return WAITING_REPLY


async def admin_send_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    target_id = ctx.user_data.get("reply_to")
    if not target_id:
        await update.message.reply_text("Нет активного чата для ответа.")
        return ConversationHandler.END

    reply_text = update.message.text
    try:
        await ctx.bot.send_message(
            target_id,
            f"📩 *Ответ от исполнителя:*\n\n{reply_text}",
            parse_mode="Markdown",
        )
        await update.message.reply_text("✅ Ответ доставлен клиенту!")
    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось доставить: {e}")
    ctx.user_data.pop("reply_to", None)
    return ConversationHandler.END


# ─── /help ────────────────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Как пользоваться ботом:*\n\n"
        "1️⃣ Нажми /start\n"
        "2️⃣ Выбери тип услуги\n"
        "3️⃣ Заполни название, ТЗ, бюджет, дедлайн\n"
        "4️⃣ Подтверди и отправь заказ\n\n"
        "После отправки исполнитель свяжется с тобой напрямую или через бота.\n\n"
        "/start — новый заказ",
        parse_mode="Markdown",
    )


# ─── Отмена ───────────────────────────────────────────────────────
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Оформление отменено. Напиши /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── Точка входа ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Диалог для клиента
    client_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_TYPE:    [CallbackQueryHandler(choose_type, pattern="^(denizen|website|design|other)$")],
            ENTER_TITLE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_title)],
            ENTER_TZ:       [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_tz)],
            ENTER_BUDGET:   [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_budget)],
            ENTER_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_deadline)],
            ENTER_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contacts)],
            CONFIRM:        [CallbackQueryHandler(confirm, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Диалог ответа администратора
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_reply_button, pattern="^reply_")],
        states={
            WAITING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
                    admin_send_reply,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(client_conv)
    app.add_handler(admin_conv)
    app.add_handler(CommandHandler("help", help_cmd))

    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
