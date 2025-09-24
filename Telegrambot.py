from telegram.ext import Updater, CommandHandler
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
conn = sqlite3.connect('solo_cashmachine.db', check_same_thread=False)
cur = conn.cursor()

updater = Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'), use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied! This is Danny's private cash machine.")
        return
    cur.execute("INSERT OR IGNORE INTO player (user_id, balance, mode, created_at) VALUES (?, 0, ?, ?)",
                (user_id, 'aviation', datetime.now().isoformat()))
    conn.commit()
    update.message.reply_text("Welcome to your Cash Machine! Choose /mode <aviation|tap>, deposit via /deposit <amount>, and play at http://your-render-app.onrender.com")

def mode(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    try:
        new_mode = context.args[0].lower()
        if new_mode in ['aviation', 'tap']:
            cur.execute("UPDATE player SET mode = ? WHERE user_id = ?", (new_mode, user_id))
            conn.commit()
            update.message.reply_text(f"Mode set to {new_mode}!")
        else:
            update.message.reply_text("Usage: /mode aviation|tap")
    except IndexError:
        update.message.reply_text("Usage: /mode aviation|tap")

def deposit(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    try:
        amount = float(context.args[0])
        update.message.reply_text(f"Visit http://your-render-app.onrender.com/deposit?user_id={user_id}&amount={amount} to deposit ${amount}")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /deposit <amount>")

def balance(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    cur.execute("SELECT balance, mode FROM player WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    balance = result[0] if result else 0
    mode = result[1] if result else 'aviation'
    update.message.reply_text(f"Your balance: ${balance:.2f}\nMode: {mode}")

def riggame(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    try:
        action = context.args[0].lower()
        if action in ['win', 'lose']:
            os.environ['WIN_RATE'] = '1.0' if action == 'win' else '0.0'
            update.message.reply_text(f"Aviation game rigged to {action} next bet!")
        else:
            update.message.reply_text("Usage: /riggame win|lose")
    except IndexError:
        update.message.reply_text("Usage: /riggame win|lose")

def rigtap(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    try:
        action = context.args[0].lower()
        if actionyta == 'boost':
            os.environ['TAP_PAYOUT_RATE'] = '1.0'
            update.message.reply_text("Tap-to-Pay rigged to 100% payout next conversion!")
        else:
            update.message.reply_text("Usage: /rigtap boost")
    except IndexError:
        update.message.reply_text("Usage: /rigtap boost")

def profits(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    cur.execute("SELECT SUM(profit) FROM profits")
    total_profit = cur.fetchone()[0] or 0
    update.message.reply_text(f"Total System Profits: ${total_profit:.2f}")

def fling(update, context):
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('ADMIN_USER_ID')):
        update.message.reply_text("Access denied!")
        return
    profit = random.uniform(20, 100)
    cur.execute("SELECT balance FROM player WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    new_balance = (result[0] if result else 0) + profit
    cur.execute("INSERT OR REPLACE INTO player (user_id, balance, mode, created_at) VALUES (?, ?, ?, ?)",
                (user_id, new_balance, 'aviation', datetime.now().isoformat()))
    conn.commit()
    update.message.reply_text(f"🚀 Fling Exploit! Added ${profit:.2f} to your balance!")
    context.bot.send_message(chat_id=ADMIN_USER_ID, text=f"💰 Fling Profit: ${profit:.2f}")

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('mode', mode))
dispatcher.add_handler(CommandHandler('deposit', deposit))
dispatcher.add_handler(CommandHandler('balance', balance))
dispatcher.add_handler(CommandHandler('riggame', riggame))
dispatcher.add_handler(CommandHandler('rigtap', rigtap))
dispatcher.add_handler(CommandHandler('profits', profits))
dispatcher.add_handler(CommandHandler('fling', fling))

updater.start_polling()