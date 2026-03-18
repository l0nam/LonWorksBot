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
