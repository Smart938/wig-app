import asyncio
import logging
import os
import replicate
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8721292715:AAGUHaSwM2Q1-VbgPHhO1Jh_WTu2jbTA-Q8")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "r8_Htw4fiuk7x71wvT3IRLd4gGhb7vJrXr4Y4156")
MODEL_NAME = "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4"

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для примерки париков.\n"
        "Отправь мне фото, и я покажу, как на тебе будет выглядеть новый образ!\n\n"
        "Или нажми кнопку Menu, чтобы открыть Mini App."
    )

# Обработка фото (чат)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Фото от {user.first_name}")

    msg = await update.message.reply_text("🔄 Обрабатываю... ~20 секунд")

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

        await update.message.reply_photo(
            photo=result_url,
            caption="✨ Вот твой новый образ!"
        )

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("😔 Ошибка. Попробуй ещё раз.")

    finally:
        await msg.delete()

# Обработчик Mini App
async def tryon_handler(request):
    try:
        data = await request.post()
        photo = data['photo']
        color = data.get('color', 'Blonde')
        style = data.get('style', 'Long Layers')

        import base64
        photo_bytes = photo.file.read()
        photo_b64 = base64.b64encode(photo_bytes).decode()
        photo_url = "data:image/jpeg;base64," + photo_b64

        prompt = f"a photo of a woman img with {style.lower()} {color.lower()} hair, high quality, realistic"
        logger.info(f"Mini App запрос: {prompt}")

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

# Запуск веб-сервера в отдельном потоке
def start_web():
    web_app = web.Application()
    web_app.router.add_post('/tryon', tryon_handler)
    web.run_app(web_app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Основная функция
def main():
    # Запускаем веб-сервер в фоне
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    logger.info("Веб-сервер Mini App запущен в фоне")

    # Запускаем бота
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()