import asyncio

from config import settings

from loguru import logger

from src.resources import tags_mapping
from src.tg.media import media_uploader, Media

from src.database import crud
from src.database.db import async_session
from src.types.enums import PostStatus

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
        except Exception as e:
            await posting_notify.add_error_post(post_str)
            await tg_logger.send_log(f"Ошибка при обработке поста {post_str}:\n{e}")


async def process_single_post(post_str: str) -> None:
    post_url, tags = map(str, post_str.split())
    data = await get_post_from_url(post_url)
    logger.info(f"Полученные данные для поста: {data}")
    if "и" in tags:
        await posting_notify.msg_to_translation(data.media_paths)
        post_status = PostStatus.NEEDS_EDIT_AND_TRANSLATE
    else:
        post_status = PostStatus.NEEDS_TEXT_EDIT

    caption = format_message(data.author, post_url, tags)

    async with async_session() as session:
        create_post_result = await crud.create_post(
            session=session,
            caption=caption,
            status=post_status
        )
        attachments = await get_medias(data.media_paths)
        for i, m in enumerate(attachments):
            await crud.add_media_to_post(
                session,
                post_id=create_post_result.id,
                media_type=m.type,
                telegram_file_id=m.file_id,
                sort_order=i
            )


def format_message(author: str, post_url: str, tags: str) -> str:
    formatted_tags = get_tags_message(tags)
    return f'Оригинал: <a href="{post_url}">{author}</a>\n\n{formatted_tags}'


def get_tags_message(tags: str):
    tags_list = []
    for tag in tags:
        if tag in tags_mapping:
            tags_list.append(tags_mapping[tag])
    return " ".join(tags_list)


async def get_medias(file_paths: list[str]) -> list[Media]:
    medias = []
    for file_path in file_paths:
        media = await media_uploader.upload_media(file_path)
        medias.append(media)
        await asyncio.sleep(0.5)  # Небольшая пауза между загрузками, чтобы избежать проблем с API
    return medias