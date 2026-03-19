import logging
import os
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
    ContextTypes
)

# ─── CONFIG ──────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── STATES ──────────────────────────
(
    CHOOSE_TYPE,
    ENTER_TITLE,
    ENTER_TZ,
    ENTER_BUDGET,
    ENTER_DEADLINE,
    ENTER_CONTACTS,
    CONFIRM,
) = range(7)

# ─── DATA ────────────────────────────
SERVICE_LABELS = {
    "denizen": "🧩 Denizen Script плагин",
    "website": "🌐 Сайт",
    "design": "🎨 Дизайн",
    "other": "💡 Другое",
}

# ─── HELPERS ─────────────────────────

def is_valid_text(update: Update) -> bool:
    return bool(update.message and update.message.text)


def safe_get(mapping, key, default="Неизвестно"):
    return mapping.get(key, default)

# ─── START ───────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()

    kb = [
        [InlineKeyboardButton(label, callback_data=key)]
        for key, label in SERVICE_LABELS.items()
    ]

    await update.message.reply_text(
        "👋 <b>Привет!</b> Я принимаю заказы на:\n\n"
        "🧩 <b>Denizen Script</b> — плагины для Minecraft\n"
        "🌐 <b>Сайты</b> — лендинги, веб-приложения\n"
        "🎨 <b>Дизайн</b> — UI/UX, графика, брендинг\n\n"
        "Выбери тип работы 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return CHOOSE_TYPE

# ─── TYPE ────────────────────────────
async def choose_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    service = q.data
    ctx.user_data["service_type"] = service

    await q.edit_message_text(
        f"Отлично, выбрано: <b>{safe_get(SERVICE_LABELS, service)}</b>\n\n"
        "✏️ Напиши короткое <b>название проекта</b> (одностраничка для a-проект, скрипт на b-проект):",
        parse_mode="HTML",
    )
    return ENTER_TITLE

# ─── TITLE ───────────────────────────
async def enter_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_valid_text(update):
        return ENTER_TITLE

    ctx.user_data["title"] = update.message.text.strip()

    await update.message.reply_text(
        "📋 Напиши подробное <b>техническое задание</b>.\n\n"
        "Включи:\n"
        "• Функционал / страницы / экраны\n"
        "• Референсы (ссылки, примеры)\n"
        "• Технические требования\n"
        "• Любые важные детали",
        parse_mode="HTML",
    )
    return ENTER_TZ

# ─── TZ ──────────────────────────────
async def enter_tz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_valid_text(update):
        return ENTER_TZ

    ctx.user_data["tz"] = update.message.text.strip()

    await update.message.reply_text(
        "💰 Укажи <b>бюджет</b> (или напиши «не знаю»):",
        parse_mode="HTML",
    )
    return ENTER_BUDGET

# ─── BUDGET ──────────────────────────
async def enter_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_valid_text(update):
        return ENTER_BUDGET

    ctx.user_data["budget"] = update.message.text.strip()

    await update.message.reply_text(
        "📅 Укажи <b>дедлайн</b> — когда нужно готово? (или «не горит»):",
        parse_mode="HTML",
    )
    return ENTER_DEADLINE

# ─── DEADLINE ────────────────────────
async def enter_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_valid_text(update):
        return ENTER_DEADLINE

    ctx.user_data["deadline"] = update.message.text.strip()

    await update.message.reply_text(
        "📞 Укажи <b>контакт</b> для связи:\n"
        "Telegram (@username), email или другой мессенджер:",
        parse_mode="HTML",
    )
    return ENTER_CONTACTS

# ─── CONTACTS ────────────────────────
async def enter_contacts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_valid_text(update):
        return ENTER_CONTACTS

    ctx.user_data["contacts"] = update.message.text.strip()
    d = ctx.user_data

    preview = (
        "<b>Проверь заказ:</b>\n\n"
        f"🔹Тип: {safe_get(SERVICE_LABELS, d.get('service_type'))}\n"
        f"🔹Название: {d.get('title')}\n"
        f"🔹Бюджет: {d.get('budget')}\n"
        f"🔹Дедлайн: {d.get('deadline')}\n"
        f"🔹Контакт: {d.get('contacts')}\n\n"
        f"🔹ТЗ:\n{d.get('tz')}"
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Отправить", callback_data="yes"),
            InlineKeyboardButton("🔄 Заново", callback_data="no"),
        ]
    ])

    await update.message.reply_text(preview, parse_mode="HTML", reply_markup=kb)
    return CONFIRM

# ─── CONFIRM ─────────────────────────
async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "no":
        await q.edit_message_text("🔄 Начинаем заново...")
        return await start(update, ctx)

    d = ctx.user_data
    user = update.effective_user

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    await q.edit_message_text("✅ Заказ отправлен!")

    admin_text = (
        f"НОВЫЙ ЗАКАЗ {now}\n\n"
        f"🔹ID: {user.id}\n"
        f"🔹User: {user.full_name}\n\n"
        f"🔹Тип: {safe_get(SERVICE_LABELS, d.get('service_type'))}\n"
        f"🔹Название: {d.get('title')}\n"
        f"🔹Бюджет: {d.get('budget')}\n"
        f"🔹Дедлайн: {d.get('deadline')}\n"
        f"🔹Контакт: {d.get('contacts')}\n\n"
        f"🔹ТЗ:\n```{d.get('tz')}```"
    )

    if len(admin_text) > 4000:
        admin_text = admin_text[:4000] + "\n...[обрезано]"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"reply_{user.id}")]
    ])

    await ctx.bot.send_message(ADMIN_ID, md_escape(admin_text), reply_markup=kb)

    ctx.user_data.clear()
    return ConversationHandler.END

# ─── ADMIN REPLY ─────────────────────
async def admin_reply_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target = int(q.data.split("_")[1])
    except Exception:
        return

    ctx.user_data["reply_to"] = target
    await q.message.reply_text("Напиши ответ:")

async def admin_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not is_valid_text(update):
        return

    target = ctx.user_data.get("reply_to")
    if not target:
        return

    try:
        await ctx.bot.send_message(target, f"Ответ:\n{update.message.text}")
        await update.message.reply_text("Отправлено")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка при отправке")

    ctx.user_data.pop("reply_to", None)

# ─── MAIN ────────────────────────────

def main():
    if not BOT_TOKEN or not ADMIN_ID:
        raise ValueError("BOT_TOKEN или ADMIN_ID не заданы")

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_TYPE: [CallbackQueryHandler(choose_type)],
            ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_title)],
            ENTER_TZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_tz)],
            ENTER_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_budget)],
            ENTER_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_deadline)],
            ENTER_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contacts)],
            CONFIRM: [CallbackQueryHandler(confirm)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_reply_button, pattern="^reply_"))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_send))

    app.run_polling()

if __name__ == "__main__":
    main()
