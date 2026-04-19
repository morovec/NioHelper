import traceback

from logger import logger
from aiogram import Dispatcher

import asyncio

from config import tg_bot as tg
from src.database.db import init_db

dp = Dispatcher()

async def main():
    include_routers()
    await init_db()

    try:
        await dp.start_polling(tg)
    finally:
        await dp.storage.close()
        await tg.session.close()

def include_routers():
    from src.tg import routers
    for router in routers:
        dp.include_router(router)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Bot stopped by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())