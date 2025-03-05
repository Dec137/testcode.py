import json
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Constants
TELEGRAM_TOKEN = '7031299961:AAH_hIZhOMe0wKLK4wZD_W49eVyNJN9tUqM'
TARGET_URL = 'https://giaxstore.com/collections/sconti-selezionati'

# Create a Flask app for Render's health check
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

@web_app.route('/health')
def health_check():
    return "OK", 200

# Telegram Bot Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to GiaxStore Discount Bot! 🛍️\n"
        "Use /discounts to see current offers"
    )

async def get_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Fetch and parse HTML
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(TARGET_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract product data
        script = soup.find('script', {'id': 'shop-js-analytics'})
        data = json.loads(script.text.split('meta = ')[1].split(';\n')[0])
        
        # Process products
        products = []
        for product in data['products']:
            for variant in product['variants']:
                products.append({
                    "title": product.get('title', 'No Title'),
                    "price": f"€{variant['price'] / 100:.2f}",
                    "sku": variant.get('sku', 'N/A'),
                    "image": f"https://giaxstore.com{product['image']['src']}",
                    "url": f"https://giaxstore.com{product['url']}"
                })
        
        # Send products to user
        for product in products:
            keyboard = [[InlineKeyboardButton("View Product", url=product['url'])]]
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=product['image'],
                caption=f"🏷️ *{product['title']}*\n"
                       f"💶 Price: {product['price']}\n"
                       f"📦 SKU: {product['sku']}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            
        await update.message.reply_text("That's all our current discounts! 🎉")
        
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        await update.message.reply_text(f"⚠️ Error fetching products: {str(e)}")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Exception while handling an update: {context.error}")

# Main function
def main():
    # Start Flask app in a separate thread for Render's health check
    import threading
    threading.Thread(target=lambda: web_app.run(host="0.0.0.0", port=10000)).start()

    # Start the Telegram bot
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("discounts", get_discounts))
    
    # Add error handler
    app.add_error_handler(error_handler)

    # Start polling
    logging.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
