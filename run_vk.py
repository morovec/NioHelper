from logger import logger
import sys
import asyncio
from config import settings

from src.database.db import init_db
from vkbottle.bot import Bot as VKBot
from vkbottle.bot import BotLabeler

def load_labelers(labeler: BotLabeler):
    """Load labelers inside function to avoid circular imports"""
    from src.vk import labelers
    for labeler_item in labelers:
        labeler.load(labeler_item)

        

def main():
    if not settings:
        logger.critical("Configuration could not be loaded. Ensure config.yaml exists.")
        sys.exit(1)

    labeler = BotLabeler()
    load_labelers(labeler)
    bot = VKBot(token=settings.vk.bot_token,
                labeler=labeler)

    asyncio.run(init_db())
    bot.run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Bot stopped by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")