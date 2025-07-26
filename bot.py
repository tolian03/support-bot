import logging, random, time, requests, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# === Настройки ===
BOT_TOKEN       = os.environ['BOT_TOKEN']
GOOGLE_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSdi7Ix4mXx5_RCIGFyTchGVoyXCtx39Xw0gYb7raaW9xklYUw/formResponse'
FORM_FIELDS = {
    'username':    'entry.1368847426',
    'timestamp':   'entry.191041080',
    'telegram_id': 'entry.280481905',
    'problem_type':'entry.1561160532',
    'quest_type':  'entry.742312363',
    'issue_type':  'entry.208008286',
    'details':     'entry.2023070220',
    'email':       'entry.1413654436',
    'wallet':      'entry.507047698',
}
CHOOSING, TSQ, OTHER, CREATE_ISSUE, OTHER_Q, EMAIL, WALLET = range(7)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(u, c):
    kb = [[InlineKeyboardButton("1. Time Soul квесты", callback_data='ts')],
          [InlineKeyboardButton("2. Другое",        callback_data='other')]]
    await u.message.reply_text("Привет! С чем проблема?", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSING

async def choosing(u, c):
    q = u.callback_query; await q.answer()
    c.user_data['problem_type'] = q.data
    if q.data == 'other':
        await q.edit_message_text("Опишите вашу проблему:")
        return OTHER
    kb = [[InlineKeyboardButton("Create account на Mystery Cave + Telegram", callback_data='quest_create')],
          [InlineKeyboardButton("Download TimeSoul + 1 Practice",           callback_data='quest_download')],
          [InlineKeyboardButton("Buy TimeBox NFT for $TTS",                callback_data='quest_buy')],
          [InlineKeyboardButton("Complete daily practice",                 callback_data='quest_daily')]]
    await q.edit_message_text("Выберите квест:", reply_markup=InlineKeyboardMarkup(kb))
    return TSQ

async def other(u, c):
    c.user_data['details'] = u.message.text
    return await submit(u, c)

async def tsq(u, c):
    q = u.callback_query; await q.answer()
    c.user_data['quest_type'] = q.data
    if q.data == 'quest_create':
        kb = [[InlineKeyboardButton("Не засчитывается", callback_data='issue_not')],
              [InlineKeyboardButton("Нет кода",          callback_data='issue_code')]]
        await q.edit_message_text("Что не так с регистрацией?", reply_markup=InlineKeyboardMarkup(kb))
        return CREATE_ISSUE
    await q.edit_message_text("Опишите проблему по этому квесту:")
    return OTHER_Q

async def create_issue(u, c):
    q = u.callback_query; await q.answer()
    c.user_data['issue_type'] = q.data
    await q.edit_message_text("Введите вашу почту:")
    return EMAIL

async def other_q(u, c):
    c.user_data['details'] = u.message.text
    await u.message.reply_text("Введите вашу почту:")
    return EMAIL

async def email(u, c):
    c.user_data['email'] = u.message.text
    await u.message.reply_text("Введите ваш EVM-кошелёк:")
    return WALLET

async def wallet(u, c):
    c.user_data['wallet'] = u.message.text
    return await submit(u, c)

def make_ticket(): return f"TICKET-{int(time.time())}-{random.randint(1000,9999)}"

async def submit(u, c):
    user = u.effective_user
    data = {
        FORM_FIELDS['username']:    user.username or user.full_name,
        FORM_FIELDS['timestamp']:   time.strftime("%Y-%m-%d %H:%M:%S"),
        FORM_FIELDS['telegram_id']: str(user.id),
        FORM_FIELDS['problem_type']:c.user_data.get('problem_type',''),
        FORM_FIELDS['quest_type']:  c.user_data.get('quest_type',''),
        FORM_FIELDS['issue_type']:  c.user_data.get('issue_type',''),
        FORM_FIELDS['details']:     c.user_data.get('details',''),
        FORM_FIELDS['email']:       c.user_data.get('email',''),
        FORM_FIELDS['wallet']:      c.user_data.get('wallet',''),
    }
    try: requests.post(GOOGLE_FORM_URL, data=data)
    except: pass
    ticket = make_ticket()
    await u.effective_message.reply_text(f"Готово! Ваш тикет #{ticket}.")
    return ConversationHandler.END

async def cancel(u, c):
    await u.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING:      [CallbackQueryHandler(choosing)],
            OTHER:         [MessageHandler(filters.TEXT & ~filters.COMMAND, other)],
            TSQ:           [CallbackQueryHandler(tsq)],
            CREATE_ISSUE:  [CallbackQueryHandler(create_issue)],
            OTHER_Q:       [MessageHandler(filters.TEXT & ~filters.COMMAND, other_q)],
            EMAIL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            WALLET:        [MessageHandler(filters.TEXT & ~filters.COMMAND, wallet)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
