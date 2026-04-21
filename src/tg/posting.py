import asyncio
import random

from requests import session
from sqlalchemy import delete

from config import settings, tg_bot as bot

from loguru import logger

from src.resources import tags_mapping
from src.tg.media import media_uploader, Media

from src.database import crud
from src.database.db import async_session
from src.database.models import Post, PostMedia
from src.types.enums import PostStatus

from .notify import posting_notify, tg_logger
from src.handlers.scrapers import get_post_from_url

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from aiogram.types import (
    InputMediaPhoto,
    InputMediaVideo
)

class EditPostStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_media = State()

post_router = Router(name=__name__)

@post_router.message(Command("publish"), F.chat.id == settings.admin_chat_id)
async def post(message: Message):
    await publish_post()

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


async def publish_post():
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

# ==========================================================================================
# ========== Post Edit text ==============================
# ==========================================================================================


from src.tg.keyboards.posts import post_edit_keyboard, post_edit_keyboard_without_delete, post_translate_keyboard

async def edit_post_caption(post_id: int, new_caption: str) -> bool:
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            return False
        
        caption = post.caption.split("\n\n")
        if len(caption) == 2:
            new_caption = new_caption + "\n\n" + caption[0] + "\n\n" + caption[1]
        else:
            new_caption = new_caption + "\n\n" + caption[1] + "\n\n" + caption[2]

        post.caption = new_caption
        if post.status == PostStatus.NEEDS_TEXT_EDIT:
            post.status = PostStatus.READY
        elif post.status == PostStatus.NEEDS_EDIT_AND_TRANSLATE:
            post.status = PostStatus.NEEDS_TRANSLATE
        session.add(post)
        await session.commit()
        return True


async def edit_post_caption_full(post_id: int, new_caption: str) -> bool:
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            return False
        
        post.caption = new_caption
        session.add(post)
        await session.commit()
        return True

@post_router.message(Command("get_random_edit_post"), F.chat.id == settings.admin_chat_id)
async def get_random_edit_post(message: Message):
    await message.delete()
    await asyncio.sleep(0.5)  # Небольшая пауза, чтобы избежать проблем с API
    async with async_session() as session:
        posts = await crud.get_posts(session)
        edit_posts = [p for p in posts if p.status in (PostStatus.NEEDS_TEXT_EDIT, PostStatus.NEEDS_EDIT_AND_TRANSLATE)]
        if not edit_posts:
            await message.answer("Нет постов для редактирования.")
            return
        
        post = random.choice(edit_posts)
        media_list = await crud.get_media_by_post_id(session, post.id)
        text = f"Пост ID: {post.id}\n\n{post.caption}"
        await send_media_with_caption(media_list, message, text, post_edit_keyboard(post.id))

async def get_edit_post_by_id(message: Message, post_id: int):
    await asyncio.sleep(0.5)  # Небольшая пауза, чтобы избежать проблем с API
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            await message.answer("Пост не найден.")
            return
        media_list = await crud.get_media_by_post_id(session, post.id)
        text = f"Пост ID: {post.id}\n\n{post.caption}"
        await send_media_with_caption(media_list, message, text, post_edit_keyboard(post.id))

async def send_media_with_caption(media_list: list[PostMedia], message: Message, text: str, keyboard):
    if len(media_list) == 1:
        item = media_list[0]
        if item.media_type == "photo":
            await message.answer_photo(item.telegram_file_id, caption=text, reply_markup=keyboard)
        elif item.media_type == "video":
            await message.answer_video(item.telegram_file_id, caption=text, reply_markup=keyboard)
    else:
        album = []
        for i, item in enumerate(media_list):
            if item.media_type == "photo":
                album.append(InputMediaPhoto(
                    media=item.telegram_file_id,
                    caption=text if i == 0 else None
                ))
            elif item.media_type == "video":
                album.append(InputMediaVideo(
                    media=item.telegram_file_id,
                    caption=text if i == 0 else None
                ))
        await message.answer_media_group(album)
        await message.answer("Клавиатура для альбома", reply_markup=keyboard)


@post_router.callback_query(F.data.startswith("get_random_edit_post"), F.message.chat.id == settings.admin_chat_id)
async def get_random_edit_post_callback(callback: CallbackQuery):
    await get_random_edit_post(callback.message)


@post_router.callback_query(F.data.startswith("edit_text"), F.message.chat.id == settings.admin_chat_id)
async def edit_text_callback(callback: CallbackQuery, state: FSMContext):
    post_id = int(callback.data.split(":")[1])
    await state.update_data(post_id=post_id)
    await callback.message.answer("Введите новый текст для поста:")
    await state.set_state(EditPostStates.waiting_for_text)


@post_router.message(EditPostStates.waiting_for_text, F.chat.id == settings.admin_chat_id)
async def process_new_text(message: Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    new_text = message.text
    success = await edit_post_caption(post_id, new_text)
    if success:
        await get_edit_post_by_id(message, post_id)
    else:
        await message.answer("Ошибка при обновлении текста поста. Ничего не произошло.")
        await get_edit_post_by_id(message, post_id)
    await state.clear()


@post_router.callback_query(F.data.startswith("delete_post"), F.message.chat.id == settings.admin_chat_id)
async def delete_post_callback(callback: CallbackQuery):
    post_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        await crud.delete_post(session, post_id)
    await callback.message.edit_caption(caption=f"{callback.message.caption}\n\nПост успешно удален!",
                                        reply_markup=post_edit_keyboard_without_delete(post_id)
                                        )


@post_router.callback_query(F.data.startswith("hide"), F.message.chat.id == settings.admin_chat_id)
async def hide_post_callback(callback: CallbackQuery):
    await callback.message.delete()
