import os
from dataclasses import dataclass
from typing import List

from config import settings, tg_bot as bot
from src.tg.notify import tg_logger
from aiogram.types import FSInputFile

import traceback

@dataclass
class Media:
    type: str
    file_id: str

class MediaUploader:
    async def upload_media(self, file_path: str) -> Media:
        if not os.path.exists(file_path):
            await tg_logger.send_log(f"Файл не найден: {file_path}")
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        try:
            # Определяем тип файла по расширению
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in ['.jpg', '.jpeg', '.png']:
                photo_file = FSInputFile(file_path)
                storage_msg = await bot.send_photo(
                    chat_id=settings.admin_chat_id,
                    message_thread_id=settings.logs_thread_id,
                    photo=photo_file,
                )
                return Media(type="photo", file_id=storage_msg.photo[-1].file_id)
                    
            elif file_ext in ['.mp4']:
                video_file = FSInputFile(file_path)
                storage_msg = await bot.send_video(
                    chat_id=settings.admin_chat_id,
                    message_thread_id=settings.logs_thread_id,
                    video=video_file,
                )
                return Media(type="video", file_id=storage_msg.video.file_id)
                    
        except Exception as ex:
            await tg_logger.send_log(f"Ошибка при загрузке файла {file_path}: {traceback.format_exc()}")
            raise ex
    
media_uploader = MediaUploader()