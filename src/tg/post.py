from config import settings, vk_user as vk

from loguru import logger

from datetime import datetime, timezone, timedelta
from src.resources import tags_mapping

from src.vk.media import media_uploader
from src.handlers import time_from_timestamp

from .notify import posting_notify, tg_logger
from src.handlers.scrapers import get_post_from_url

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import traceback

post_router = Router(name=__name__)

hours = [8, 10, 12, 14, 16, 18, 20, 22] #Moscow | UTC +7

async def get_occupied_times() -> set[int]:
    occupied_times = set()
    
    for offset in [0, 100]:
        try:
            data = await vk.api.wall.get(
                offset=offset,
                count=100,
                domain=f"club{settings.vk.group_id}",
                filter="postponed"
            )

            occupied_times.update(
                item.date for item in data.items
            )
            await tg_logger.send_log(f"Получил запланированные посты!\n{occupied_times}")
            if data.count <= 100:
                break

        except Exception as e:
            logger.error(f"VK API Error: {e}")
            break

    return occupied_times

async def get_free_time(post_amount: int) -> list[int]:
    occupied = await get_occupied_times()
    hours = [5, 7, 9, 11, 13, 15, 17, 19]  # UTC | Moscow +3 UTC
    
    free_times = []
    
    # Текущая дата и время
    now = datetime.now(timezone.utc)
    current_date = now.replace(minute=0, second=0, microsecond=0)
    
    # Вычисляем дату через неделю от текущего момента
    one_week_from_now = now + timedelta(days=7)
    
    while len(free_times) < post_amount:
        for h in hours:
            slot = current_date.replace(hour=h)
            
            # Проверяем, что слот в будущем
            if slot <= now:
                continue
                
            # Проверяем, что слот не раньше чем через неделю
            if slot < one_week_from_now:
                continue
                
            ts = int(slot.timestamp())
            
            # Проверяем, что слот не занят
            if ts not in occupied:
                free_times.append(ts)
                
                if len(free_times) == post_amount:
                    break
        
        current_date += timedelta(days=1)
    
    await tg_logger.send_log(f"Возвращаю массив свободных временных слотов. \n{free_times}")
    return free_times

def get_tags_message(tags: str):
    tags_list = []
    for tag in tags:
        if tag in tags_mapping:
            tags_list.append(tags_mapping[tag])
    
    return " ".join(tags_list)

def format_message(author: str, tags: str) -> str:
    formatted_tags = get_tags_message(tags)
    return f"Автор: {author}\n\n{formatted_tags}"

async def process_single_post(post_str: str, publish_time: int) -> str:
    try:
        post_url, tags = map(str, post_str.split())
        data = await get_post_from_url(post_url)
        await tg_logger.send_log(f"Получил данные с поста:\nАвтор:{data.author}")
    except ValueError as e:
        await posting_notify.add_error_post(post_str)
        await tg_logger.send_log(f"Ошибка при получении данных поста\n{str(e)}")
        raise e

    try:
        await tg_logger.send_log("Загружаю файлы на сервера ВК...")
        attachments = await media_uploader.upload_media(file_paths=data.media_paths,
                                                        post_url=post_url)
        await tg_logger.change_log("Файлы успешно загружены!")
    except Exception as e:
        await tg_logger.change_log("Ошибка при загрузке файлов на сервера ВК")
        await posting_notify.add_error_post(post_str)
        raise e

    if "и" in tags:
        tg_logger.send_log(f"Отправляю файлы на перевод!")
        await posting_notify.msg_to_translation(data.media_paths)
        await tg_logger.change_log("Файлы успешно отправлены!")

    message = format_message(data.author, tags)
    await tg_logger.send_log("Отправляю пост в отложку...")
    post_info = await vk.api.wall.post(
        message=message,
        attachments=attachments,
        publish_date=publish_time,
        owner_id=-settings.vk.group_id,
        from_group=1
    )
    await tg_logger.change_log("Отправил пост в отложку!")

    return f"https://vk.com/wall{-settings.vk.group_id}_{post_info.post_id}"

async def handle_posting_data(posting_data: str) -> None:
    free_post_times = await get_free_time(len(posting_data))
    time_idx = 0
    for post_str in posting_data:
        try:
            current_slot = free_post_times[time_idx]
            
            success_link = await process_single_post(post_str, current_slot)
            
            log_msg = f"{success_link} {time_from_timestamp(current_slot)}"
            await posting_notify.add_success_post(log_msg)
            
            time_idx += 1
            
        except Exception as e:
            logger.critical(e)
            await tg_logger.send_log(f"Ошибка при обработке поста {post_str}:\n{traceback.format_exc()}")
            continue

@post_router.message(Command("post"), F.chat.id == settings.admin_chat_id)
async def post(message: Message):
    if message.message_thread_id != settings.posting_thread_id:
        return 0
    
    posting_data = message.text.split("\n")[1:]
    logger.info(f"Handling post data:\n{posting_data}")
    await posting_notify.msg_to_posting(
        text=f"Посты(Всего {len(posting_data)}):"
        )
    await handle_posting_data(posting_data)