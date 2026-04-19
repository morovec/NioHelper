from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.tg.posting import publish_post

from aiogram import Router
from .notify import tg_logger
from src.resources import messages

from loguru import logger

switcher_router = Router(name=__name__)

@switcher_router.startup()
async def on_startup() -> None:
    logger.info("Bot powered on!")
    await tg_logger.send_log(messages.startup)

    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Moscow"))

    scheduler.add_job(
        publish_post,
        trigger=CronTrigger(hour="8,10,12,14,16,18,20,22", minute=0),
        misfire_grace_time=300, # Если бот лежал, у него есть 5 минут, чтобы нагнать
        max_instances=1 # Защита от двойного запуска
    )

    scheduler.start()

@switcher_router.shutdown()
async def on_shutdown() -> None:
    logger.info("Bot powered off!")
    await tg_logger.send_log(messages.shutdown)