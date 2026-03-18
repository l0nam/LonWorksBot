
import logging import os from telegram import ( Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove ) from telegram.ext import ( Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes ) from telegram.helpers import escape_markdown from datetime import datetime

logging.basicConfig( format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO ) logger = logging.getLogger(name)

( CHOOSE_TYPE, ENTER_TITLE, ENTER_TZ, ENTER_BUDGET, ENTER_DEADLINE, ENTER_CONTACTS, CONFIRM, ) = range(7)

BOT_TOKEN = os.environ["BOT_TOKEN"] ADMIN_ID = int(os.environ["ADMIN_ID"])

SERVICE_LABELS = { "denizen": "🧩 Denizen Script плагин", "website": "🌐 Сайт", "design": "🎨 Дизайн", "other": "💡 Другое", }

─── Utils ─────────────────────────────

def esc(text: str) -> str: return escape_markdown(text or "—", version=2)

async def ensure_text(update, state): if not update.message or not update.message.text: await update.message.reply_text("❌ Пожалуйста, отправь текст.") return state return None

─── /start ───────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE): ctx.user_data.clear()

kb = [
    [InlineKeyboardButton(label, callback_data=key)]
    for key, label in SERVICE_LABELS.items()
]

await update.message.reply_text(
    "👋 *Привет\!* Выбери тип работы 👇",
    parse_mode="MarkdownV2",
    reply_markup=InlineKeyboardMarkup(kb),
)
return CHOOSE_TYPE

─── Тип ──────────────────────────────

async def choose_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE): q = update.callback_query await q.answer()

ctx.user_data["service_type"] = q.data

await q.edit_message_text(
    f"Выбрано: *{esc(SERVICE_LABELS[q.data])}*\n\nВведите название проекта:",
    parse_mode="MarkdownV2",
)
return ENTER_TITLE

─── Название ─────────────────────────

async def enter_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE): if not update.message.text: return ENTER_TITLE

ctx.user_data["title"] = update.message.text

await update.message.reply_text("📋 Напиши ТЗ:")
return ENTER_TZ

─── ТЗ ──────────────────────────────

async def enter_tz(update: Update, ctx: ContextTypes.DEFAULT_TYPE): if not update.message.text: return ENTER_TZ

ctx.user_data["tz"] = update.message.text

await update.message.reply_text("💰 Бюджет?")
return ENTER_BUDGET

─── Бюджет ──────────────────────────

async def enter_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE): if not update.message.text: return ENTER_BUDGET

ctx.user_data["budget"] = update.message.text

await update.message.reply_text("📅 Дедлайн?")
return ENTER_DEADLINE

─── Дедлайн ─────────────────────────

async def enter_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE): if not update.message.text: return ENTER_DEADLINE

ctx.user_data["deadline"] = update.message.text

await update.message.reply_text("📞 Контакт?")
return ENTER_CONTACTS

─── Контакты ────────────────────────

async def enter_contacts(update: Update, ctx: ContextTypes.DEFAULT_TYPE): if not update.message.text: return ENTER_CONTACTS

ctx.user_data["contacts"] = update.message.text
d = ctx.user_data

preview = (
    f"*Проверь заказ:*\n\n"
    f"Тип: {esc(SERVICE_LABELS[d['service_type']])}\n"
    f"Название: {esc(d['title'])}\n"
    f"Бюджет: {esc(d['budget'])}\n"
    f"Дедлайн: {esc(d['deadline'])}\n"
    f"Контакт: {esc(d['contacts'])}\n\n"
    f"ТЗ:\n{esc(d['tz'])}"
)

kb = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Отправить", callback_data="yes"),
        InlineKeyboardButton("🔄 Заново", callback_data="no"),
    ]
])

await update.message.reply_text(preview, parse_mode="MarkdownV2", reply_markup=kb)
return CONFIRM

─── Подтверждение ───────────────────

async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE): q = update.callback_query await q.answer()

if q.data == "no":
    await q.edit_message_text("Начни заново: /start")
    ctx.user_data.clear()
    return ConversationHandler.END

d = ctx.user_data
user = update.effective_user

now = datetime.now().strftime("%d.%m.%Y %H:%M")

await q.edit_message_text("✅ Заказ отправлен!")

admin_text = (
    f"НОВЫЙ ЗАКАЗ {now}\n\n"
    f"ID: {user.id}\n"
    f"User: {user.full_name}\n\n"
    f"Тип: {SERVICE_LABELS[d['service_type']]}\n"
    f"Название: {d['title']}\n"
    f"Бюджет: {d['budget']}\n"
    f"Дедлайн: {d['deadline']}\n"
    f"Контакт: {d['contacts']}\n\n"
    f"ТЗ:\n{d['tz']}"
)

if len(admin_text) > 4096:
    admin_text = admin_text[:4000] + "\n...[обрезано]"

kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("Ответить", callback_data=f"reply_{user.id}")]
])

await ctx.bot.send_message(ADMIN_ID, admin_text, reply_markup=kb)

ctx.user_data.clear()
return ConversationHandler.END

─── Ответ админа ────────────────────

async def admin_reply_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE): q = update.callback_query await q.answer()

if update.effective_user.id != ADMIN_ID:
    return

target = int(q.data.split("_")[1])
ctx.user_data["reply_to"] = target

await q.message.reply_text("Напиши ответ:")

async def admin_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE): if update.effective_user.id != ADMIN_ID: return

target = ctx.user_data.get("reply_to")
if not target:
    return

try:
    await ctx.bot.send_message(target, f"Ответ:\n{update.message.text}")
    await update.message.reply_text("Отправлено")
except Exception as e:
    await update.message.reply_text(f"Ошибка: {e}")

ctx.user_data.pop("reply_to", None)

─── main ────────────────────────────

def main(): app = Application.builder().token(BOT_TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_TYPE: [CallbackQueryHandler(choose_type)],
        ENTER_TITLE: [MessageHandler(filters.TEXT, enter_title)],
        ENTER_TZ: [MessageHandler(filters.TEXT, enter_tz)],
        ENTER_BUDGET: [MessageHandler(filters.TEXT, enter_budget)],
        ENTER_DEADLINE: [MessageHandler(filters.TEXT, enter_deadline)],
        ENTER_CONTACTS: [MessageHandler(filters.TEXT, enter_contacts)],
        CONFIRM: [CallbackQueryHandler(confirm)],
    },
    fallbacks=[CommandHandler("cancel", start)],
)

app.add_handler(conv)
app.add_handler(CallbackQueryHandler(admin_reply_button, pattern="^reply_"))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_send))

app.run_polling()

if name == "main": main()    "denizen":  "🧩 Denizen Script плагин",
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
        "✏️ Напиши короткое *название* проекта (1–2 предложения):",
        parse_mode="Markdown",
    )
    return ENTER_TITLE


# ─── Шаг 2: название ─────────────────────────────────────────────
async def enter_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(
        "📋 Теперь напиши подробное *техническое задание*.\n\n"
        "_Чем детальнее — тем точнее будет оценка._\n\n"
        "Включи:\n"
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
    if update.effective_user.id != ADMIN_ID:
        return
    target_id = int(query.data.split("_")[1])
    # Сохраняем в bot_data (общий стейт), чтобы следующий MessageHandler поймал
    ctx.bot_data["admin_reply_to"] = target_id
    await query.message.reply_text(
        f"✏️ Напиши ответ клиенту (ID: `{target_id}`).\n"
        "Просто отправь следующее сообщение сюда 👇",
        parse_mode="Markdown",
    )


async def admin_send_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    target_id = ctx.bot_data.get("admin_reply_to")
    if not target_id:
        return  # не ждём ответа — игнорируем обычные сообщения

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
    ctx.bot_data.pop("admin_reply_to", None)


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
        per_message=False,
        per_chat=True,
    )

    app.add_handler(client_conv)

    # Кнопка «Ответить» и ответ админа — простые хендлеры, без ConversationHandler
    app.add_handler(CallbackQueryHandler(admin_reply_button, pattern="^reply_"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
        admin_send_reply,
    ))

    app.add_handler(CommandHandler("help", help_cmd))

    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
