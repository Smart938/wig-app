import asyncio
import logging
import replicate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ТВОИ ТОКЕНЫ (замени на свои)
TELEGRAM_TOKEN = "8721292715:AAGUHaSwM2Q1-VbgPHhO1Jh_WTu2jbTA-Q8"
REPLICATE_API_TOKEN = "r8_Rnpd9lTmptVDgpiL6v1NmeU4af7iVgo2eips6"
MODEL_NAME = "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4"


# Инициализация Replicate
import os
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для примерки париков.\n"
        "Отправь мне фото, и я покажу, как на тебе будет выглядеть новый образ!\n\n"
        "Или нажми кнопку Menu, чтобы открыть Mini App."
    )


# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(f"Получено фото от {user.first_name}")


    # Сообщаем, что начали обработку
    processing_msg = await update.message.reply_text("🔄 Обрабатываю фото... Это займёт около 20 секунд.")


    try:
        # Получаем файл фото
        photo_file = await update.message.photo[-1].get_file()
        photo_url = photo_file.file_path


        # Запускаем модель Replicate
        output = replicate.run(
                MODEL_NAME,
                input={
                    "input_image": photo_url,
                    "prompt": "a photo of a woman img with long blonde hair, high quality, realistic",
                    "style_name": "Photographic (Default)",
                    "num_outputs": 1
                }
            )


        # Получаем результат
        result_url = output[0] if isinstance(output, list) else output


        # Отправляем результат
        await update.message.reply_photo(
            photo=result_url,
            caption="✨ Вот твой новый образ!"
        )


    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            "😔 Произошла ошибка при обработке фото. Попробуй ещё раз."
        )


    finally:
        await processing_msg.delete()


# Основная функция с веб-сервером для Mini App
def main():
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики для чата
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запускаем веб-сервер для Mini App (параллельно с ботом)
    from aiohttp import web
    
    async def tryon_handler(request):
        """Обработчик запроса от Mini App"""
        try:
            data = await request.post()
            photo = data['photo']
            color = data.get('color', 'Blonde')
            style = data.get('style', 'Long Layers')
            
            # Сохраняем фото временно
            photo_bytes = photo.file.read()
            photo_url = "data:image/jpeg;base64," + __import__('base64').b64encode(photo_bytes).decode()
            
            # Запускаем модель
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
    
    # Запускаем веб-сервер на порту 8080
    web_app = web.Application()
    web_app.router.add_post('/tryon', tryon_handler)
    
    async def run_web():
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("Веб-сервер Mini App запущен на порту 8080")
    
    # Запускаем и бота, и веб-сервер
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(run_web())
    
    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()