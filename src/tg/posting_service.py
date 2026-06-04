import asyncio
import random

from loguru import logger

from config import settings, tg_bot as bot

from src.resources import tags_mapping
from src.tg.media import media_uploader, Media

from src.database import crud
from src.database.db import async_session
from src.database.models import Post, PostMedia
from src.types.enums import PostStatus

from .notify import posting_notify, tg_logger
from src.handlers.scrapers import get_post_from_url
from src.tg.keyboards.posts import (
    post_edit_keyboard,
    post_album_edit_keyboard,
    post_edit_media_keyboard,
    post_album_edit_media_keyboard,
    post_ready_keyboard,
    post_album_ready_keyboard,
)

from aiogram.types import (
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)


def format_message(author: str, post_url: str, tags: str) -> str:
    formatted_tags = get_tags_message(tags)
    return f'Оригинал: <a href="{post_url}">{author}</a>\n\n{formatted_tags}'


def get_tags_message(tags: str) -> str:
    tags_list = []
    for tag in tags:
        if tag in tags_mapping:
            tags_list.append(tags_mapping[tag])
    return " ".join(tags_list)


async def get_medias(file_paths: list[str]) -> list[Media]:
    medias: list[Media] = []
    for file_path in file_paths:
        media = await media_uploader.upload_media(file_path)
        medias.append(media)
        await asyncio.sleep(0.5)
    return medias


async def process_single_post(post_str: str) -> int:
    await asyncio.sleep(1)
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
        return create_post_result.id


async def handle_posting_data(posting_data: list[str]) -> None:
    for i, post_str in enumerate(posting_data):
        try:
            await asyncio.sleep(0.5)
            post_id = await process_single_post(post_str)

            log_msg = f"Пост ...{post_str[-10:-2]} Добавлен! ID: {post_id} | №{i+1}"
            await posting_notify.add_success_post(log_msg)
        except Exception as e:
            await asyncio.sleep(0.5)
            await posting_notify.add_error_post(post_str)
            await tg_logger.send_log(f"Ошибка при обработке поста {post_str}:\n{e}")


async def publish_post() -> int:
    async with async_session() as session:
        ready_posts = await crud.get_ready_posts(session)

        logger.info(f"Найдено постов для публикации: {len(ready_posts)}")
        tg_logger.send_log(f"Найдено постов для публикации: {len(ready_posts)}")

        if not ready_posts:
            return 0

        post = random.choice(ready_posts)
        logger.info(f"Публикуем пост ID {post.id} с caption: {post.caption}")

        media_list = await crud.get_media_by_post_id(session, post.id)

        if len(media_list) == 1:
            item = media_list[0]
            if item.media_type == "photo":
                await bot.send_photo(settings.telegram.group_id, item.telegram_file_id, caption=post.caption)
            elif item.media_type == "video":
                await bot.send_video(settings.telegram.group_id, item.telegram_file_id, caption=post.caption)
            await crud.delete_post(session, post.id)
            return 0

        album = []
        for i, item in enumerate(media_list):
            if item.media_type == "photo":
                album.append(InputMediaPhoto(
                    media=item.telegram_file_id,
                    caption=post.caption if i == 0 else None
                ))
            elif item.media_type == "video":
                album.append(InputMediaVideo(
                    media=item.telegram_file_id,
                    caption=post.caption if i == 0 else None
                ))

        await bot.send_media_group(chat_id=settings.telegram.group_id, media=album)
        await crud.delete_post(session, post.id)
        return post.id


async def edit_post_caption(post_id: int, new_text: str) -> bool:
    """
    Edit only the text part of post caption, preserving author info and hashtags.
    Finds "Оригинал:" marker to separate text from metadata.
    """
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            return False

        # Find metadata section (everything from "Оригинал:" onwards)
        caption = post.caption
        metadata_start_idx = caption.find('Оригинал:')
        
        if metadata_start_idx != -1:
            # Extract metadata (author info and hashtags)
            metadata = caption[metadata_start_idx:]
        else:
            # Fallback if "Оригинал:" not found (shouldn't happen)
            metadata = ''

        # Build new caption with new text and preserved metadata
        post.caption = f'{new_text}\n\n{metadata}' if metadata else new_text
        
        if post.status == PostStatus.NEEDS_TEXT_EDIT:
            post.status = PostStatus.READY
        elif post.status == PostStatus.NEEDS_EDIT_AND_TRANSLATE:
            post.status = PostStatus.NEEDS_IMAGE_TRANSLATE
        session.add(post)
        await session.commit()
        return True


async def make_post_text(post: Post) -> str:
    """
    Return full post text with ID, status and caption for display.
    """
    return f"Пост ID: {post.id}\nСтатус: {post.status}\n\n{post.caption}"


def extract_post_text_only(caption: str) -> str:
    """
    Extract only the text part from caption (before "Оригинал:").
    Safely handles captions with multiple edits (2-3+ sections).
    """
    metadata_start_idx = caption.find('Оригинал:')
    
    if metadata_start_idx != -1:
        # Get everything before "Оригинал:" and remove trailing \n\n
        text = caption[:metadata_start_idx].rstrip()
        # Remove the last "\n\n" separator if present
        if text.endswith('\n\n'):
            text = text[:-2]
        return text
    else:
        # Fallback: if "Оригинал:" not found, assume entire caption is text
        return caption


def parse_callback_data(data: str) -> tuple[str, int | None, int | None]:
    parts = data.split(":")
    if len(parts) == 3:
        return parts[0], int(parts[1]), int(parts[2])
    if len(parts) == 2:
        return parts[0], int(parts[1]), None
    return parts[0], None, None


async def get_keyboard_for_post(post_id: int, media_list: list[PostMedia], mode: str = "edit", index: int = 0):
    if len(media_list) <= 1:
        if mode == "ready":
            return post_ready_keyboard(post_id)
        if mode == "translate":
            return post_edit_media_keyboard(post_id)
        return post_edit_keyboard(post_id)

    if mode == "ready":
        return post_album_ready_keyboard(post_id, index, len(media_list))
    if mode == "translate":
        return post_album_edit_media_keyboard(post_id, index, len(media_list))
    return post_album_edit_keyboard(post_id, index, len(media_list))


async def send_media_with_caption(media_list: list[PostMedia], message: Message, text: str, keyboard, index: int = 0):
    if index < 0 or index >= len(media_list):
        index = 0

    item = media_list[index]
    if item.media_type == "photo":
        await message.answer_photo(item.telegram_file_id, caption=text, reply_markup=keyboard)
    elif item.media_type == "video":
        await message.answer_video(item.telegram_file_id, caption=text, reply_markup=keyboard)
    else:
        await message.answer_document(item.telegram_file_id, caption=text, reply_markup=keyboard)
