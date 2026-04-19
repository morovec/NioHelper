from config import settings

from loguru import logger

from src.resources import tags_mapping
from src.tg.media import media_uploader

from .notify import posting_notify, tg_logger
from src.handlers.scrapers import get_post_from_url

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import traceback

post_router = Router(name=__name__)

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


async def handle_posting_data(posting_data: str) -> None:
    time_idx = 0
    for post_str in posting_data:
        try:
            await process_single_post(post_str)
            
            log_msg = f"Пост успешно добавлен в базу данных!"
            await posting_notify.add_success_post(log_msg)
            
            time_idx += 1
        except:
            await posting_notify.add_error_post(post_str)
            await tg_logger.send_log(f"Ошибка при обработке поста {post_str}:\n{traceback.format_exc()}")


async def process_single_post(post_str: str) -> str:
    post_url, tags = map(str, post_str.split())
    data = await get_post_from_url(post_url)

    attachments = await get_media_ids(data.media_paths)

    # attachments = await media_uploader.upload_media(file_paths=data.media_paths,
    #                                                 post_url=post_url)

    if "и" in tags:
        await posting_notify.msg_to_translation(data.media_paths)

    message = format_message(data.author, post_url, tags)
    # post_info = await vk.api.wall.post(
    #     message=message,
    #     attachments=attachments,
    #     publish_date=publish_time,
    #     owner_id=-settings.vk.group_id,
    #     from_group=1
    # )
    # return f"https://vk.com/wall{-settings.vk.group_id}_{post_info.post_id}"


def format_message(author: str, post_url: str, tags: str) -> str:
    formatted_tags = get_tags_message(tags)
    return f'Оригинал: <a href="{post_url}">{author}</a>\n\n{formatted_tags}'


def get_tags_message(tags: str):
    tags_list = []
    for tag in tags:
        if tag in tags_mapping:
            tags_list.append(tags_mapping[tag])


async def get_media_ids(file_paths: list[str]) -> list[str]:
    media_ids = await media_uploader.upload_media(file_path)
    return media_ids