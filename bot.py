import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
conn = sqlite3.connect('/mnt/data/solo_cashmachine.db', check_same_thread=False)
cur = conn.cursor()

async def start(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied! This is Danny's private cash machine.")
        return
    cur.execute("INSERT OR IGNORE INTO player (user_id, balance, mode, created_at) VALUES (?, 0,?,?)",
                (user_id, 'aviation', datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text("Welcome to your Cash Machine! Use /mode <aviation|tap>, /deposit <amount>, and play at http://your-render-app.onrender.com")

async def mode(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    try:
        new_mode = context.args[0].lower()
        if new_mode in ['aviation', 'tap']:
            cur.execute("UPDATE player SET mode =? WHERE user_id = ?", (new_mode, user_id))
            conn.commit()
            await update.message.reply_text(f"Mode set to {new_mode}!")
        else:
            await update.message.reply_text("Usage: /mode aviation|tap")
    except IndexError:
        await update.message.reply_text("Usage: /mode aviation|tap")

async def deposit(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    try:
        amount = float(context.args[0])
        await update.message.reply_text(f"Visit http://your-render-app.onrender.com/deposit?user_id={user_id}&amount={amount} to deposit${amount:.2f}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /deposit <amount>")

async def balance(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    cur.execute("SELECT balance, mode FROM player WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    balance = result[0] if result else 0
    mode = result[1] if result else 'aviation'
    await update.message.reply_text(f"Your balance:${balance:.2f}\nMode: {mode}")

async def riggame(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    try:
        action = context.args[0].lower()
        if action in ['win', 'lose']:
            os.environ['WIN_RATE'] = '1.0' if action == 'win' else '0.0'
            await update.message.reply_text(f"Aviation game rigged to {action} next bet!")
        else:
            await update.message.reply_text("Usage: /riggame win|lose")
    except IndexError:
        await update.message.reply_text("Usage: /riggame win|lose")

async def rigtap(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    try:
        action = context.args[0].lower()
        if action == 'boost':
            os.environ['TAP_PAYOUT_RATE'] = '1.0'
            await update.message.reply_text("Tap-to-Pay rigged to 100% payout next conversion!")
        else:
            await update.message.reply_text("Usage: /rigtap boost")
    except IndexError:
        await update.message.reply_text("Usage: /rigtap boost")

async def profits(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    cur.execute("SELECT SUM(profit) FROM profits")
    total_profit = cur.fetchone()[0] or 0
    await update.message.reply_text(f"Total System Profits:${total_profit:.2f}")

async def hackcash(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    profit = random.uniform(20, 100)
    cur.execute("SELECT balance FROM player WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    new_balance = (result[0] if result else 0) + profit
    cur.execute("INSERT OR REPLACE INTO player (user_id, balance, mode, created_at) VALUES (?,?,?,?)",
                (user_id, new_balance, 'aviation', datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"💸 Hacked the System! Added${profit:.2f} to your balance!")
    await context.bot.send_message(chat_id=user_id, text=f"💰 Hack Profit:${profit:.2f}")

async def fling(update, context):
    user_id = update.message.from_user.id
    if user_id!= int(os.getenv('ADMIN_USER_ID')):
        await update.message.reply_text("Access denied!")
        return
    profit = random.uniform(50, 150)
    cur.execute("SELECT balance FROM player WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    new_balance = (result[0] if result else 0) + profit
    cur.execute("INSERT OR REPLACE INTO player (user_id, balance, mode, created_at) VALUES (?,?,?,?)",
                (user_id, new_balance, 'aviation', datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"🚀 Fling Exploit! Added${profit:.2f} to your balance!")
    await context.bot.send_message(chat_id=user_id, text=f"💰 Fling Profit:${profit:.2f}")

def main():
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('mode', mode))
    app.add_handler(CommandHandler('deposit', deposit))
    app.add_handler(CommandHandler('balance', balance))
    app.add_handler(CommandHandler('riggame', riggame))
    app.add_handler(CommandHandler('rigtap', rigtap))
    app.add_handler(CommandHandler('profits', profits))
    app.add_handler(CommandHandler('hackcash', hackcash))
    app.add_handler(CommandHandler('fling', fling))
    app.run_polling()

if __name__ == "__main__":
    main()
