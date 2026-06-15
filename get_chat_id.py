import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = "ТВОЙ_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message()
async def get_id(message: types.Message):
    print("CHAT ID:", message.chat.id)
    await message.answer(f"CHAT ID: {message.chat.id}")


async def main():
    print("RUNNING ID CHECK BOT")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())