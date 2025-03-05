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
AMAZON_URL = 'https://www.amazon.com/s?k=discounts'  # Amazon search URL for discounts

# Telegram Bot Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Amazon Discount Bot! 🛍️\n"
        "Use /discounts to see current offers"
    )

async def get_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Fetch and parse HTML
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(AMAZON_URL, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract product data
        products = []
        for item in soup.select('div.s-result-item'):
            try:
                title = item.select_one('h2 a span').text.strip()
                price = item.select_one('.a-price .a-offscreen')
                price = price.text.strip() if price else "Price not available"
                link = item.select_one('h2 a')['href']
                link = f"https://www.amazon.com{link}" if link else "Link not available"
                image = item.select_one('img.s-image')['src'] if item.select_one('img.s-image') else "Image not available"

                products.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": image
                })
            except Exception as e:
                logging.error(f"Error parsing product: {e}")
                continue

        # Send products to user
        if not products:
            await update.message.reply_text("No products found. 😢")
            return

        for product in products[:5]:  # Limit to 5 products to avoid spamming
            keyboard = [[InlineKeyboardButton("View Product", url=product['link'])]]
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=product['image'],
                caption=f"🏷️ *{product['title']}*\n"
                       f"💶 Price: {product['price']}",
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
