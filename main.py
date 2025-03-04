import json
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = '7031299961:AAHy0waGghDRRR4ll593q6vRs7PCDchxUdo'
TARGET_URL = 'https://giaxstore.com/collections/sconti-selezionati'

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
            )
            
        await update.message.reply_text("That's all our current discounts! 🎉")
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching products: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("discounts", get_discounts))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
