import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    raise ValueError("ОШИБКА: Нет токена! Создай файл .env с BOT_TOKEN=...")