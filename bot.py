import logging
import sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ১. কনফিগারেশন
TOKEN = "8938601509:AAGk1BrRWyTkw_Pomzvq2hNihuKXF1j7qFQ"
CHANNEL_LINK = "https://t.me/aserningbd"
ADMIN_USERNAME = "Huray6" # আপনার ইউজারনেম দিন
ADMIN_ID = 5628585499 # এখানে আপনার টেলিগ্রাম Numeric ID দিন
GMAIL_PRICE = 15.0 # প্রতি জিমেইলের দাম (BDT)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ২. Flask সার্ভার (Render Free Web Service-এ বট সচল রাখার জন্য)
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Telegram Bot is running 24/7!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ৩. ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gmail_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        balance = row[0]
    else:
        cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0.0))
        conn.commit()
        balance = 0.0
    conn.close()
    return balance

def update_user_balance(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?', (user_id, amount, amount))
    conn.commit()
    conn.close()

# ৪. মূল হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_balance(user_id)
    keyboard = [
        [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Verify", callback_data='verify')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 বটের সব ফিচার ব্যবহার করতে প্রথমে আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন এবং নিচে Verify বাটনে চাপ দিন:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

async def show_main_menu(query):
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Gmail", callback_data='buy_gmail'), InlineKeyboardButton("💰 Sell Gmail", callback_data='sell_gmail')],
        [InlineKeyboardButton("✈️ Buy Telegram", callback_data='buy_tg'), InlineKeyboardButton("💳 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("👨‍💻 Admin Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎉 ভেরিফিকেশন সফল হয়েছে!\n\nমূল মেনু থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন:"
    await query.edit_message_text(text, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 মূল মেনুতে ফিরুন", callback_data='back_to_menu')]])

    if query.data == 'verify':
        await show_main_menu(query)
        
    elif query.data == 'buy_gmail':
        balance = get_user_balance(user_id)
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, account_data FROM gmail_stock LIMIT 1')
        stock_item = cursor.fetchone()
        
        if not stock_item:
            await query.edit_message_text("❌ দুঃখিত, বর্তমানে কোনো জিমেইল স্টকে নেই! পরে চেষ্টা করুন।", reply_markup=back_keyboard)
        elif balance < GMAIL_PRICE:
            await query.edit_message_text(f"⚠️ আপনার পর্যাপ্ত ব্যালেন্স নেই!\n\nজিমেইলের দাম: {GMAIL_PRICE} BDT\nআপনার ব্যালেন্স: {balance:.2f} BDT\n\nদয়া করে Wallet থেকে Add Money করুন।", reply_markup=back_keyboard)
        else:
            gmail_id, gmail_acc = stock_item
            cursor.execute('DELETE FROM gmail_stock WHERE id = ?', (gmail_id,))
            conn.commit()
            update_user_balance(user_id, -GMAIL_PRICE)
            
            text = f"🎉 **জিমেইল কেনা সফল হয়েছে!**\n\n📧 **অ্যাকাউন্ট বিবরণ:**\n`{gmail_acc}`\n\nক্লিয়ার ব্যালেন্স: {balance - GMAIL_PRICE:.2f} BDT"
            await query.edit_message_text(text, reply_markup=back_keyboard, parse_mode='Markdown')
        conn.close()
        
    elif query.data == 'sell_gmail':
        text = f"💰 জিমেইল বিক্রি করতে সরাসরি এডমিনের সাথে যোগাযোগ করুন:\n👉 {ADMIN_USERNAME}"
        await query.edit_message_text(text, reply_markup=back_keyboard)
        
    elif query.data == 'buy_tg':
        text = f"✈️ টেলিগ্রাম একাউন্ট কিনতে এডমিনকে নক দিন:\n👉 {ADMIN_USERNAME}"
        await query.edit_message_text(text, reply_markup=back_keyboard)
        
    elif query.data == 'wallet':
        balance = get_user_balance(user_id)
        wallet_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Money", callback_data='add_money'), InlineKeyboardButton("➖ Cash Out", callback_data='cash_out')],
            [InlineKeyboardButton("🔙 মূল মেনুতে ফিরুন", callback_data='back_to_menu')]
        ])
        await query.edit_message_text(f"💳 **Wallet / Balance**\n\n🆔 ইউজার আইডি: `{user_id}`\n💰 আপনার বর্তমান ব্যালেন্স: **{balance:.2f} BDT**\n\nনিচের অপশন থেকে নির্বাচন করুন:", reply_markup=wallet_keyboard, parse_mode='Markdown')

    elif query.data in ['add_money', 'cash_out']:
        action_name = "টাকা ডিপোজিট/এড" if query.data == 'add_money' else "ক্যাশ আউট/উইথড্র"
        pm_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💖 bKash", callback_data=f'{query.data}_bkash'), InlineKeyboardButton("🧡 Nagad", callback_data=f'{query.data}_nagad')],
            [InlineKeyboardButton("💛 Binance", callback_data=f'{query.data}_binance')],
            [InlineKeyboardButton("🔙 ওয়ালেটে ফিরুন", callback_data='wallet')]
        ])
        await query.edit_message_text(f"💳 **{action_name}** করার জন্য পেমেন্ট মেথড বেছে নিন:", reply_markup=pm_keyboard, parse_mode='Markdown')

    elif query.data.startswith('add_money_') or query.data.startswith('cash_out_'):
        method = query.data.split('_')[-1].capitalize()
        is_add = "Add Money" if "add_money" in query.data else "Cash Out"
        text = f"⚙️ **{method} ({is_add})**\n\nআপনার ইউজার আইডি (`{user_id}`) সহ এডমিনকে সরাসরি মেসেজ দিন:\n👉 {ADMIN_USERNAME}"
        wallet_back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ওয়ালেটে ফিরুন", callback_data='wallet')]])
        await query.edit_message_text(text, reply_markup=wallet_back_keyboard, parse_mode='Markdown')
        
    elif query.data == 'support':
        text = f"👨‍💻 যেকোনো প্রয়োজনে এডমিনের সাথে যোগাযোগ করুন:\n👉 {ADMIN_USERNAME}"
        await query.edit_message_text(text, reply_markup=back_keyboard)
        
    elif query.data == 'back_to_menu':
        await show_main_menu(query)

# ৫. এডমিন কমান্ডসমূহ
async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("ব্যবহারের নিয়ম: `/addstock email:pass`", parse_mode='Markdown')
        return
    acc_data = " ".join(context.args)
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO gmail_stock (account_data) VALUES (?)', (acc_data,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ স্টকে নতুন জিমেইল যুক্ত করা হয়েছে:\n`{acc_data}`", parse_mode='Markdown')

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user = int(context.args[0])
        amount = float(context.args[1])
        update_user_balance(target_user, amount)
        await update.message.reply_text(f"✅ ইউজার `{target_user}` এর ওয়ালেটে {amount} BDT যোগ করা হয়েছে।", parse_mode='Markdown')
    except:
        await update.message.reply_text("ব্যবহারের নিয়ম: `/addbal USER_ID AMOUNT` (যেমন: `/addbal 123456789 100`)", parse_mode='Markdown')

async def check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM gmail_stock')
    count = cursor.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📦 বর্তমান জিমেইল স্টক: {count} টি")

if __name__ == '__main__':
    # Flask সার্ভার ব্যাকগ্রাউন্ডে রান করানো
    keep_alive()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addstock", add_stock))
    app.add_handler(CommandHandler("addbal", add_balance))
    app.add_handler(CommandHandler("stock", check_stock))
    app.add_handler(CallbackQueryHandler(button_click))
    print("Bot started with Database & Flask...")
    app.run_polling()