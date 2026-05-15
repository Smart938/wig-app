import asyncio
import logging
import os
import replicate
import base64
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8948455136:AAFKh5YWXDVoHMELoLJq8nEAXPgtd_WgEY4")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "r8_Htw4fiuk7x71wvT3IRLd4gGhb7vJrXr4Y4156")
MODEL_NAME = "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4"

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# ====== ТЕЛЕГРАМ БОТ ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Medical Wig Try-On!\n\n"
        "I help you see how different medical wigs look on you — privately and at your own pace.\n\n"
        "👇 Try it now:\n"
        "t.me/MedicalWigBot/wigs"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Фото от {user.first_name}")
    msg = await update.message.reply_text("🔄 Processing... ~20 seconds")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_url = photo_file.file_path
        output = replicate.run(
            MODEL_NAME,
            input={
                "input_image": photo_url,
                "prompt": "a photo of a woman img with long blonde hair, high quality, realistic",
                "style_name": "Photographic (Default)",
                "num_outputs": 1
            }
        )
        result_url = output[0] if isinstance(output, list) else output
        await update.message.reply_photo(photo=result_url, caption="✨ Your new look!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("😔 Error. Please try again.")
    finally:
        await msg.delete()

# ====== ВЕБ-СЕРВЕР ДЛЯ MINI APP ======

async def tryon_handler(request):
    try:
        data = await request.post()
        photo = data['photo']
        color = data.get('color', 'Blonde')
        style = data.get('style', 'Long Layers')

        photo_bytes = photo.file.read()
        photo_b64 = base64.b64encode(photo_bytes).decode()
        photo_url = "data:image/jpeg;base64," + photo_b64

        prompt = f"a photo of a woman img with {style.lower()} {color.lower()} hair, high quality, realistic"
        logger.info(f"Mini App: {prompt}")

        output = replicate.run(
            MODEL_NAME,
            input={
                "input_image": photo_url,
                "prompt": prompt,
                "style_name": "Photographic (Default)",
                "num_outputs": 1
            }
        )

        result_url = output[0] if isinstance(output, list) else output
        return web.json_response({"result_url": result_url})

    except Exception as e:
        logger.error(f"Mini App error: {e}")
        return web.json_response({"error": str(e)}, status=500)

def start_web():
    web_app = web.Application()
    web_app.router.add_post('/tryon', tryon_handler)
    web.run_app(web_app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ====== ЗАПУСК ======

def main():
    # Веб-сервер в фоне
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    logger.info("Web server for Mini App started on port " + os.environ.get('PORT', '8080'))

    # Telegram бот
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()