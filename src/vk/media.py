import os
from typing import List

from vkbottle.tools import PhotoWallUploader, DocWallUploader, VideoUploader
from vkbottle_types.objects import VideoVideoFull

from config import settings, vk_user as vk
from src.resources import media_title, description_part
from src.tg.notify import tg_logger

import requests
import traceback

class MediaUploader:
    def __init__(self):
        self.photo_uploader = PhotoWallUploader(vk.api)
        self.doc_uploader = DocWallUploader(vk.api)
        self.video_uploader = VideoUploader(vk.api)

    async def upload_media(self, file_paths: List[str], post_url: str) -> List[str]:
        """
        Загружает медиафайлы на сервер VK и возвращает массив attachments
        
        Args:
            file_paths: список путей к медиафайлам
            
        Returns:
            Список строк в формате attachments (photo{owner_id}_{id}, doc{owner_id}_{id})
        """
        attachments = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                tg_logger.send_log(f"Файл не найден: {file_path}")
                continue

            description = description_part + post_url
                
            try:
                # Определяем тип файла по расширению
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png']:
                    # Загружаем фото
                    photo = await self.photo_uploader.upload(str(file_path),
                                                             settings.vk.group_id,
                                                             caption=description)
                    attachments.append(photo)
                    
                elif file_ext in ['.mp4']:
                    # Загружаем видео
                    video = await self.video_uploader.upload(str(file_path),
                                                             name=media_title,
                                                             description=description,
                                                             group_id=settings.vk.group_id,
                                                             repeat=True)
                    attachments.append(video)
                    
                else:
                    doc = await self.doc_uploader.upload(str(file_path),
                                                         group_id=settings.vk.group_id,
                                                         title=description)
                    attachments.append(doc)
                    
            except Exception as ex:
                await tg_logger.send_log(f"Ошибка при загрузке файла {file_path}: {traceback.format_exc()}")
                raise ex
                
        return attachments
    
media_uploader = MediaUploader()

class MediaDownloader:
    def __init__(self):
        pass

    def video(self, video: VideoVideoFull):
        access_key = video.access_key
        owner_id = video.owner_id
        video_id = video.id

        video = f"{owner_id}_{video_id}_{access_key}" if access_key else f"{owner_id}_{video_id}"
        user_agent = "KateMobileAndroid/99 lite-535 (Android 11; SDK 30; arm64-v8a; asus Zenfone Max Pro M1; ru)"
        headers = {"user-agent": user_agent}

        video_data = requests.post("https://api.vk.com/method/video.get",
                                   headers=headers,
                                   data={
                                       "access_token": settings.vk.user_token,
                                       "owner_id": owner_id,
                                       "videos": video,
                                       "extended": 1,
                                       "v": "5.92"
                                       }).json()

        video_urls = video_data["response"]["items"][0]["files"]
        video_url = ""
        for video_size in ("mp4_144", "mp4_240", "mp4_480", "mp4_720", "mp4_1080"):
            if video_size in video_urls.keys():
                video_url = video_urls[video_size]

        return {"url": video_url,
                "headers": headers}
    
media_downloader = MediaDownloader()