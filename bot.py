import asyncio
import logging
import os
import replicate
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8721292715:AAHxdwQCbbv5q0SJiUgib7Ql7tSr4D9SruA")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "r8_Htw4fiuk7x71wvT3IRLd4gGhb7vJrXr4Y4156")
MODEL_NAME = "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4"

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для примерки париков.\n"
        "Отправь мне фото, и я покажу, как на тебе будет выглядеть новый образ!\n\n"
        "Или нажми кнопку Menu, чтобы открыть Mini App."
    )

# Обработка фото
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
        await update.message.reply_photo(photo=result_url, caption="✨ Вот твой новый образ!")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("😔 Ошибка. Попробуй ещё раз.")

    finally:
        await msg.delete()

# Точка входа
if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Бот запущен!")
    app.run_polling()
