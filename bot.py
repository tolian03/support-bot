import logging
import random
import time
import os

from logging.handlers import RotatingFileHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from models import init_db, SessionLocal, Ticket

# ================== НАСТРОЙКИ ЛОГИРОВАНИЯ ==================
handler = RotatingFileHandler(
    'bot.log',
    maxBytes=5_000_000,
    backupCount=5
)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
# =========================================================

# Состояния ConversationHandler
CHOOSING_PROBLEM, TS_QUEST, OTHER_DETAILS, CREATE_ACCT_ISSUE, \
OTHER_QUEST_DETAILS, COLLECT_EMAIL, COLLECT_WALLET = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт: выбор основной категории."""
    kb = [
        [InlineKeyboardButton("1. Time Soul квесты", callback_data='ts_quests')],
        [InlineKeyboardButton("2. Другое",        callback_data='other')],
    ]
    await update.message.reply_text("Привет! С чем проблема?", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSING_PROBLEM

async def choosing_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора между квестами и «другое»."""
    q = update.callback_query
    await q.answer()
    context.user_data['problem_type'] = q.data
    if q.data == 'other':
        await q.edit_message_text("Опишите вашу проблему:")
        return OTHER_DETAILS

    kb = [
        [InlineKeyboardButton("Create account на Mystery Cave + Telegram", callback_data='quest_create')],
        [InlineKeyboardButton("Download TimeSoul + 1 Practice",           callback_data='quest_download')],
        [InlineKeyboardButton("Buy TimeBox NFT for $TTS",                callback_data='quest_buy')],
        [InlineKeyboardButton("Complete daily practice",                 callback_data='quest_daily')],
    ]
    await q.edit_message_text("Выберите квест:", reply_markup=InlineKeyboardMarkup(kb))
    return TS_QUEST

async def other_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор детального описания для «Другое»."""
    context.user_data['details'] = update.message.text
    return await submit(update, context)

async def ts_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор конкретного квеста и, при первом квесте, уточнение типа проблемы."""
    q = update.callback_query
    await q.answer()
    context.user_data['quest_type'] = q.data
    if q.data == 'quest_create':
        kb = [
            [InlineKeyboardButton("Не засчитывается", callback_data='issue_not')],
            [InlineKeyboardButton("Нет кода",          callback_data='issue_code')],
        ]
        await q.edit_message_text("Что не так с регистрацией?", reply_markup=InlineKeyboardMarkup(kb))
        return CREATE_ACCT_ISSUE

    await q.edit_message_text("Опишите проблему по этому квесту:")
    return OTHER_QUEST_DETAILS

async def create_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор типа проблемы для первого квеста."""
    q = update.callback_query
    await q.answer()
    context.user_data['issue_type'] = q.data
    await q.edit_message_text("Введите вашу почту:")
    return COLLECT_EMAIL

async def other_quest_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор деталей для остальных квестов."""
    context.user_data['details'] = update.message.text
    await update.message.reply_text("Введите вашу почту:")
    return COLLECT_EMAIL

async def collect_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор e‑mail."""
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Введите ваш EVM‑кошелёк:")
    return COLLECT_WALLET

async def collect_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сбор кошелька и финализация."""
    context.user_data['wallet'] = update.message.text
    return await submit(update, context)

def make_ticket_number() -> str:
    """Генерация уникального номера, если нужно."""
    return f"TICKET-{int(time.time())}-{random.randint(1000,9999)}"

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет тикет в SQLite и отсылает пользователю ответ."""
    user = update.effective_user

    # Сохраняем в базу
    db = SessionLocal()
    ticket = Ticket(
        telegram_id=str(user.id),
        username=user.username or user.full_name,
        problem_type=context.user_data.get('problem_type', ''),
        quest_type=context.user_data.get('quest_type', ''),
        issue_type=context.user_data.get('issue_type', ''),
        details=context.user_data.get('details', ''),
        email=context.user_data.get('email', ''),
        wallet=context.user_data.get('wallet', ''),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # ▼▼▼ Если хотите дополнительную отправку в Google Form, раскомментируйте:
    # try:
    #     data = { ... }  # заполнить аналогично старой версии
    #     requests.post(GOOGLE_FORM_URL, data=data)
    # except:
    #     pass
    # ▲▲▲

    await update.effective_message.reply_text(
        f"Готово! Ваш тикет №{ticket.id}. Мы скоро свяжемся с вами."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена Conversation."""
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.environ['BOT_TOKEN']).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_PROBLEM:      [CallbackQueryHandler(choosing_problem)],
            OTHER_DETAILS:         [MessageHandler(filters.TEXT & ~filters.COMMAND, other_details)],
            TS_QUEST:              [CallbackQueryHandler(ts_quest)],
            CREATE_ACCT_ISSUE:     [CallbackQueryHandler(create_issue)],
            OTHER_QUEST_DETAILS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, other_quest_details)],
            COLLECT_EMAIL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_email)],
            COLLECT_WALLET:        [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_wallet)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    # Инициализируем SQLite-базу (создаёт tickets.db и таблицы, если их нет)
    init_db()
    main()
