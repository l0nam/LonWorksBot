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
from telegram.helpers import escape_markdown
from datetime import datetime

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(
    CHOOSE_TYPE,
    ENTER_TITLE,
    ENTER_TZ,
    ENTER_BUDGET,
    ENTER_DEADLINE,
    ENTER_CONTACTS,
    CONFIRM,
) = range(7)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

SERVICE_LABELS = {
    "denizen": "🧩 Denizen Script плагин",
    "website": "🌐 Сайт",
    "design": "🎨 Дизайн",
    "other": "💡 Другое",
}

# ─── Utils ─────────────────────────────

def esc(text: str) -> str:
    return escape_markdown(text or "—", version=2)

async def ensure_text(update, state):
    if not update.message or not update.message.text:
        await update.message.reply_text("❌ Пожалуйста, отправь текст.")
        return state
    return None

# ─── /start ───────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()

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
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return CHOOSE_TYPE

# ─── Тип ──────────────────────────────
async def choose_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    ctx.user_data["service_type"] = q.data

    await q.edit_message_text(
        f"Отлично, выбрано: *{esc(SERVICE_LABELS[q.data])}*\n\n✏️ Напиши короткое *название проекта* (одностраничка для a-проект, скрипт на b-проект):",
        parse_mode="MarkdownV2",
    )
    return ENTER_TITLE

# ─── Название ─────────────────────────
async def enter_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return ENTER_TITLE

    ctx.user_data["title"] = update.message.text

    await update.message.reply_text("📋 Напиши подробное *техническое задание*.\n\n"
        "Включи:\n"
        "• Функционал / страницы / экраны\n"
        "• Референсы (ссылки, примеры)\n"
        "• Технические требования\n"
        "• Любые важные детали")
    return ENTER_TZ

# ─── ТЗ ──────────────────────────────
async def enter_tz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return ENTER_TZ

    ctx.user_data["tz"] = update.message.text

    await update.message.reply_text("💰 Укажи *бюджет* (или напиши «не знаю»):")
    return ENTER_BUDGET

# ─── Бюджет ──────────────────────────
async def enter_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return ENTER_BUDGET

    ctx.user_data["budget"] = update.message.text

    await update.message.reply_text("📅 Укажи *дедлайн* — когда нужно готово? (или «не горит»):")
    return ENTER_DEADLINE

# ─── Дедлайн ─────────────────────────
async def enter_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return ENTER_DEADLINE

    ctx.user_data["deadline"] = update.message.text

    await update.message.reply_text("📞 Укажи *контакт* для связи:\n"
        "Telegram (@username), email или другой мессенджер:",)
    return ENTER_CONTACTS

# ─── Контакты ────────────────────────
async def enter_contacts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return ENTER_CONTACTS

    ctx.user_data["contacts"] = update.message.text
    d = ctx.user_data

    preview = (
        f"*Проверь заказ:*\n\n"
        f"🔹Тип: {esc(SERVICE_LABELS[d['service_type']])}\n"
        f"🔹Название: {esc(d['title'])}\n"
        f"🔹Бюджет: {esc(d['budget'])}\n"
        f"🔹Дедлайн: {esc(d['deadline'])}\n"
        f"🔹Контакт: {esc(d['contacts'])}\n\n"
        f"🔹ТЗ:\n{esc(d['tz'])}"
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Отправить", callback_data="yes"),
            InlineKeyboardButton("🔄 Заново", callback_data="no"),
        ]
    ])

    await update.message.reply_text(preview, parse_mode="MarkdownV2", reply_markup=kb)
    return CONFIRM

# ─── Подтверждение ───────────────────
async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

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
        f"🔹ID: {user.id}\n"
        f"🔹User: {user.full_name}\n\n"
        f"🔹Тип: {SERVICE_LABELS[d['service_type']]}\n"
        f"🔹Название: {d['title']}\n"
        f"🔹Бюджет: {d['budget']}\n"
        f"🔹Дедлайн: {d['deadline']}\n"
        f"🔹Контакт: {d['contacts']}\n\n"
        f"🔹ТЗ:\n{d['tz']}"
    )

    if len(admin_text) > 4096:
        admin_text = admin_text[:4000] + "\n...[обрезано]"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"reply_{user.id}")]
    ])

    await ctx.bot.send_message(ADMIN_ID, admin_text, reply_markup=kb)

    ctx.user_data.clear()
    return ConversationHandler.END

# ─── Ответ админа ────────────────────
async def admin_reply_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    target = int(q.data.split("_")[1])
    ctx.user_data["reply_to"] = target

    await q.message.reply_text("Напиши ответ:")

async def admin_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    target = ctx.user_data.get("reply_to")
    if not target:
        return

    try:
        await ctx.bot.send_message(target, f"Ответ:\n{update.message.text}")
        await update.message.reply_text("Отправлено")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

    ctx.user_data.pop("reply_to", None)

# ─── main ────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

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

if __name__ == "__main__":
    main()
    
