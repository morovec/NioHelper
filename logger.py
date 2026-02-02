import sys
from loguru import logger
import os

# Create logs directory if not exists
if not os.path.exists("logs"):
    os.makedirs("logs")

import os
from config import settings

# Ensure log directory exists
log_file_path = "logs/bot.log"
if settings:
    log_level = settings.logging.level
    log_file_path = settings.logging.file
    rotation = settings.logging.rotation
else:
    log_level = "INFO"
    rotation = "10 MB"

log_dir = os.path.dirname(log_file_path)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure Loguru
logger.remove()
logger.add(
    sys.stdout, 
    colorize=True, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level=log_level
)

logger.add(
    log_file_path,
    rotation=rotation,
    level=log_level,
    compression="zip"
)

__all__ = ["logger"]
