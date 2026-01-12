import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import BOT_TOKEN
from bot.database.init import init_db
from bot.handlers import user, drop, orders, admin
from bot.middlewares import AdminMiddleware
from bot.config import YOUR_ADMIN_ID

async def main() -> None:
    """Main function to start the bot."""
    # Initialize database
    init_db()

    # Create bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Include routers
    dp.include_router(user.router)
    dp.include_router(drop.router)
    dp.include_router(orders.router)
    dp.include_router(admin.router)

    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())