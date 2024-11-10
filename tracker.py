from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import json
import os
import requests
import asyncio
import time

# Constants
SUBSCRIBERS_FILE = 'subscribers.json'
MEMECOIN_CONTRACT = "0x1a46467a9246f45c8c340f1f155266a26a71c07bd55d36e8d1c7d0d438a2dbc"
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_URL = os.getenv('API_URL')
HEADERS = {"Content-Type": "application/json"}

# Utility Functions
def get_latest_block_hash(url, headers):
    data = {
        "jsonrpc": "2.0",
        "method": "starknet_blockHashAndNumber",
        "params": [],
        "id": 0
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['result']['block_hash']
    return None

def get_transaction_receipt(url, headers, tx_hash):
    data = {
        "jsonrpc": "2.0",
        "method": "starknet_getTransactionReceipt",
        "params": [tx_hash],
        "id": 0
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('result')
    return None

async def check_block_for_memecoins(url, headers, block_hash, telegram_bot):
    data = {
        "jsonrpc": "2.0",
        "method": "starknet_getBlockWithTxs",
        "params": [{"block_hash": block_hash}],
        "id": 0
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        if 'result' in response_data and 'transactions' in response_data['result']:
            for tx in response_data['result']['transactions']:
                if 'calldata' in tx and len(tx['calldata']) > 0:
                    if MEMECOIN_CONTRACT in tx['calldata']:
                        tx_hash = tx.get('transaction_hash')
                        receipt = get_transaction_receipt(url, headers, tx_hash)
                        if receipt and 'events' in receipt:
                            for event in receipt['events']:
                                if event['from_address'] == MEMECOIN_CONTRACT:
                                    if 'data' in event and len(event['data']) >= 6:
                                        token_name = event['data'][1]
                                        token_name = bytes.fromhex(token_name[2:]).decode('utf-8').strip()
                                        deployed_contract = event['data'][-1]
                                        if deployed_contract.startswith('0x'):
                                            deployed_contract = '0x' + deployed_contract[2:].zfill(64)
                                        if tx_hash.startswith('0x'):
                                            tx_hash = '0x00' + tx_hash[2:]
                                        print("\n🚨 New Memecoin Detected! 🚨")
                                        print(f"Block Hash: {block_hash}")
                                        print(f"Transaction Hash: {tx_hash}")
                                        print(f"Token Name: {token_name}")
                                        print(f"Deployed Contract: {deployed_contract}")
                                        print("-" * 50)
                                        
                                        await telegram_bot.send_memecoin_alert(
                                            block_hash,
                                            token_name,
                                            tx_hash,
                                            deployed_contract
                                        )

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.subscribers = self.load_subscribers()
        self.app = Application.builder().token(token).build()
        
    def load_subscribers(self):
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def save_subscribers(self):
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(self.subscribers, f)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Welcome! Use /subscribe command to subscribe to memecoin monitoring bot.\nUse /check <block_hash> command to check a specific block."
        )

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.subscribers:
            self.subscribers.append(user_id)
            self.save_subscribers()
            await update.message.reply_text("Successfully subscribed!")
        else:
            await update.message.reply_text("You are already subscribed!")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self.save_subscribers()
            await update.message.reply_text("Successfully unsubscribed!")
        else:
            await update.message.reply_text("You are not subscribed!")

    async def send_memecoin_alert(self, block_hash, token_name, tx_hash, contract_address):
        message = (
            "🚨 New Memecoin Detected! 🚨\n\n"
            f"Block Hash: {block_hash}\n"
            f"Transaction Hash: {tx_hash}\n"
            f"Token Name: {token_name}\n"
            f"Contract Address: {contract_address}\n"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Dexscreener", url=f"https://dexscreener.com/starknet/{contract_address}"),
                InlineKeyboardButton(text="Buy on Ekubo", url=f"https://app.ekubo.org/?outputCurrency={contract_address}"),
                InlineKeyboardButton(text="Buy on Avnu", url=f"https://app.avnu.fi/en?tokenTo={contract_address}&mode=simple&tokenFrom=0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7&amount=0.001")
            ]
        ])
        
        for subscriber in self.subscribers:
            try:
                await self.app.bot.send_message(chat_id=subscriber, text=message, reply_markup=keyboard)
            except Exception as e:
                print(f"Error sending message to {subscriber}: {e}")

    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) != 1:
            await update.message.reply_text("Please enter a block hash.\nExample: /check <block_hash>")
            return
            
        block_hash = context.args[0]
        await update.message.reply_text(f"Checking block hash: {block_hash}")
        
        try:
            await check_block_for_memecoins(API_URL, HEADERS, block_hash, self)
            await update.message.reply_text("Check completed!")
        except Exception as e:
            await update.message.reply_text(f"Error occurred: {str(e)}")

async def monitor_blocks(bot):
    last_processed_block = None
    
    while True:
        try:
            current_block = get_latest_block_hash(API_URL, HEADERS)
            if current_block and current_block != last_processed_block:
                print(f"Checking block: {current_block}")
                await check_block_for_memecoins(API_URL, HEADERS, current_block, bot)
                last_processed_block = current_block
            
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(10)

async def main():
    bot = TelegramBot(BOT_TOKEN)
    
    # Add bot commands
    bot.app.add_handler(CommandHandler("start", bot.start))
    bot.app.add_handler(CommandHandler("subscribe", bot.subscribe))
    bot.app.add_handler(CommandHandler("unsubscribe", bot.unsubscribe))
    bot.app.add_handler(CommandHandler("check", bot.check))
    
    # Start the bot first
    await bot.app.initialize()
    await bot.app.start()
    
    try:
        # Run both tasks concurrently
        await asyncio.gather(
            bot.app.updater.start_polling(),
            monitor_blocks(bot)
        )
    finally:
        # Proper cleanup
        await bot.app.stop()
        await bot.app.shutdown()

if __name__ == "__main__":
    print("Starting Starknet Memecoin Monitor...")
    asyncio.run(main())