import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import age_and_city, name, description, photo

TOKEN = '7835914229:AAENF8UqemkzyMXmCZPTGfXI3icUwYEy9WI'
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'default.hostname')}/webhook"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрируем хендлеры
dp.include_router(name.router)  
dp.include_router(age_and_city.router)
dp.include_router(description.router)
dp.include_router(photo.router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
