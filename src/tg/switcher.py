from aiogram import Router
from .notify import tg_logger
from src.resources import messages

from loguru import logger

switcher_router = Router(name=__name__)

@switcher_router.startup()
async def on_startup() -> None:
    logger.info("Bot powered on!")
    await tg_logger.send_log(messages.tg_startup)

@switcher_router.shutdown()
async def on_shutdown() -> None:
    logger.info("Bot powered off!")
    await tg_logger.send_log(messages.tg_shutdown)