import json
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Constants
TELEGRAM_TOKEN = os.getenv('7031299961:AAH_hIZhOMe0wKLK4wZD_W49eVyNJN9tUqM')  # Get token from environment variable
BROWSERLESS_API_KEY = os.getenv('Rslb2B5jOC8sdzb61784bf0fbc8f4840652f1e7027')  # Browserless API key
TARGET_URL = 'https://giaxstore.com/collections/sconti-selezionati'

# Browserless API endpoint
BROWSERLESS_URL = f"https://chrome.browserless.io/content?token={BROWSERLESS_API_KEY}"

# Telegram Bot Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to GiaxStore Discount Bot! 🛍️\n"
        "Use /discounts to see current offers"
    )

async def get_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Fetch and parse HTML using Browserless
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
        }
        payload = {
            "url": TARGET_URL,
            "waitFor": 5000,  # Wait for 5 seconds to ensure the page loads
            "gotoOptions": {
                "waitUntil": "networkidle2"  # Wait until the network is idle
            }
        }
        response = requests.post(BROWSERLESS_URL, headers=headers, json=payload)
        response.raise_for_status()

        # Parse the HTML content
        from bs4 import BeautifulSoup
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
            )
            
        await update.message.reply_text("That's all our current discounts! 🎉")
        
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        await update.message.reply_text(f"⚠️ Error fetching products: {str(e)}")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Exception while handling an update: {context.error}")

# Main function
def main():
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
