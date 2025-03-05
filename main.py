import json
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Constants
TELEGRAM_TOKEN = '7031299961:AAEqNrR9hGiLALddVOihRt4lMY1kydlU5F0'  # Your Telegram bot token
TARGET_URL = 'https://giaxstore.com/collections/sconti-selezionati'

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
        if not script:
            raise ValueError("Script tag with id 'shop-js-analytics' not found!")
        
        script_text = script.text
        if 'meta = ' not in script_text:
            raise ValueError("'meta = ' not found in script tag!")
        
        data = json.loads(script_text.split('meta = ')[1].split(';\n')[0])
        
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

    # Start polling with a 1-minute interval
    logging.info("Bot is running...")
    app.run_polling(
        drop_pending_updates=True,  # Ignore pending updates
        poll_interval=60.0  # Poll every 60 seconds (1 minute)
    )

if __name__ == '__main__':
    main()
