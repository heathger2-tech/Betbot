import asyncio
import logging
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import random
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from telegram import Bot
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '7751724771'))
HOUSE_EDGE = float(os.getenv('HOUSE_EDGE', '0.1'))  # 10% house edge
WIN_RATE = float(os.getenv('WIN_RATE', '0.8'))  # 80% win rate for aviation
TAP_PAYOUT_RATE = float(os.getenv('TAP_PAYOUT_RATE', '0.9'))  # 90% payout for taps

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Initialize SQLite database
conn = sqlite3.connect('solo_cashmachine.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS player (
    user_id INTEGER PRIMARY KEY,
    balance REAL,
    mode TEXT,
    created_at TEXT)''')
cur.execute('''
CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    bet_amount REAL,
    multiplier REAL,
    outcome TEXT,
    profit REAL,
    mode TEXT,
    created_at TEXT)''')
cur.execute('''
CREATE TABLE IF NOT EXISTS profits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profit REAL,
    mode TEXT,
    created_at TEXT)''')
conn.commit()

class BetRequest(BaseModel):
    user_id: int
    bet_amount: float
    multiplier: float
    mode: str

class WithdrawRequest(BaseModel):
    user_id: int
    amount: float

async def send_telegram_notification(message):
    try:
        await telegram_bot.send_message(chat_id=ADMIN_USER_ID, text=message)
        logger.info(f"Telegram notification sent: {message}")
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")

def update_balance(user_id, amount, mode='aviation'):
    cur.execute("SELECT balance FROM player WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    new_balance = (result[0] if result else 0) + amount
    cur.execute("INSERT OR REPLACE INTO player (user_id, balance, mode, created_at) VALUES (?,?,?,?)",
                (user_id, new_balance, mode, datetime.now().isoformat()))
    conn.commit()
    return new_balance

def update_profit(profit, mode):
    cur.execute("INSERT INTO profits (profit, mode, created_at) VALUES (?,?,?)",
                (profit, mode, datetime.now().isoformat()))
    conn.commit()
    cur.execute("SELECT SUM(profit) FROM profits")
    total_profit = cur.fetchone()[0] or 0
    return total_profit

@app.post("/bet")
async def place_bet(bet: BetRequest):
    try:
        if bet.user_id != ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="Access denied")
        if bet.mode not in ['aviation', 'tap']:
            raise HTTPException(status_code=400, detail="Invalid mode")
        cur.execute("SELECT balance FROM player WHERE user_id = ?", (bet.user_id,))
        result = cur.fetchone()
        balance = result[0] if result else 0
        if balance < bet.bet_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        if bet.mode == 'aviation':
            # Aviation: Rigged RNG
            if random.random() < WIN_RATE:
                outcome = "win"
                crash_point = bet.multiplier + random.uniform(0.1, 1.0)
            else:
                outcome = "lose"
                crash_point = random.uniform(1.0, bet.multiplier - 0.1)
            player_profit = bet.bet_amount * (bet.multiplier - 1) * (1 - HOUSE_EDGE) if outcome == "win" else -bet.bet_amount
            house_profit = bet.bet_amount * HOUSE_EDGE if outcome == "lose" else -player_profit * HOUSE_EDGE
        else:
            # Tap-to-Pay: Convert taps to cash
            outcome = "win"
            crash_point = bet.multiplier
            player_profit = bet.bet_amount * TAP_PAYOUT_RATE
            house_profit = bet.bet_amount * (1 - TAP_PAYOUT_RATE)

        new_balance = update_balance(bet.user_id, player_profit, bet.mode)
        total_profit = update_profit(house_profit, bet.mode)

        cur.execute("INSERT INTO bets (user_id, bet_amount, multiplier, outcome, profit, mode, created_at) VALUES (?,?,?,?,?,?,?)",
                    (bet.user_id, bet.bet_amount, bet.multiplier, outcome, player_profit, bet.mode, datetime.now().isoformat()))
        conn.commit()

        await send_telegram_notification(
            f"🎮 {bet.mode.capitalize()} Action\nAmount: ${bet.bet_amount:.2f} @ {bet.multiplier}x\nOutcome: {outcome}\nProfit: ${player_profit:.2f}\nBalance: ${new_balance:.2f}\nTotal System Profit: ${total_profit:.2f}"
        )

        return {"status": "success", "outcome": outcome, "balance": new_balance, "crash_point": crash_point}
    except Exception as e:
        logger.error(f"Error processing {bet.mode} action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deposit")
async def deposit(user_id: int, amount: float):
    try:
        if user_id != ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="Access denied")
        response = requests.post("https://api.paystack.co/transaction/initialize",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
            json={"email": f"danny_{user_id}@example.com", "amount": int(amount * 100)}
        )
        response.raise_for_status()
        data = response.json()
        new_balance = update_balance(user_id, amount)
        await send_telegram_notification(f"💸 Deposit\nAmount: ${amount:.2f}\nNew Balance: ${new_balance:.2f}")
        return {"status": "success", "balance": new_balance, "payment_url": data['data']['authorization_url']}
    except Exception as e:
        logger.error(f"Error processing deposit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/withdraw")
async def withdraw(request: WithdrawRequest):
    try:
        if request.user_id != ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="Access denied")
        cur.execute("SELECT balance FROM player WHERE user_id = ?", (request.user_id,))
        result = cur.fetchone()
        balance = result[0] if result else 0
        if balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        # Initiate Paystack transfer (requires recipient code, setup manually in Paystack dashboard)
        response = requests.post("https://api.paystack.co/transfer",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
            json={"source": "balance", "amount": int(request.amount * 100), "recipient": "your_recipient_code"}
        )
        response.raise_for_status()
        new_balance = update_balance(request.user_id, -request.amount)
        await send_telegram_notification(f"💳 Withdrawal\nAmount: ${request.amount:.2f}\nNew Balance: ${new_balance:.2f}")
        return {"status": "success", "balance": new_balance}
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)