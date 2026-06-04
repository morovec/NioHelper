import asyncio
import random

from config import settings, tg_bot as bot

from loguru import logger

from src.database import crud
from src.database.db import async_session
from src.types.enums import PostStatus
from src.tg.posting_service import (
    edit_post_caption,
    extract_post_text_only,
    get_keyboard_for_post,
    handle_posting_data,
    make_post_text,
    parse_callback_data,
    publish_post,
    send_media_with_caption,
)
from .notify import posting_notify, tg_logger

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


# ==========================================================================================
# ========== Post Edit text ==============================
# ==========================================================================================


from src.tg.keyboards.posts import (
    post_edit_keyboard,
    post_album_edit_keyboard,
    post_edit_media_keyboard,
    post_album_edit_media_keyboard,
    post_menu_keyboard,
    post_ready_keyboard,
    post_album_ready_keyboard,
    edit_post_only_keyboard,
    post_translate_keyboard,
)

@post_router.message(Command("post_menu"), F.chat.id == settings.admin_chat_id)
async def post_menu(message: Message):
    await asyncio.sleep(0.5)
    await message.answer("Выберите категорию постов для управления:", reply_markup=post_menu_keyboard())
    

@post_router.callback_query(F.data.startswith("no_text_post") or F.data.startswith("get_random_edit_post"), F.message.chat.id == settings.admin_chat_id)
async def get_random_edit_post(callback: CallbackQuery):
    await asyncio.sleep(0.5)
    async with async_session() as session:
        posts = await crud.get_posts(session)
        edit_posts = [p for p in posts if p.status in (PostStatus.NEEDS_TEXT_EDIT, PostStatus.NEEDS_EDIT_AND_TRANSLATE)]
        if not edit_posts:
            await callback.message.answer("Нет постов для редактирования.")
            return
        
        post = random.choice(edit_posts)
        media_list = await crud.get_media_by_post_id(session, post.id)
        text = await make_post_text(post)
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="edit", index=0)
        try:
            await send_media_with_caption(media_list, callback.message, text, keyboard, index=0)
        except Exception as e:
            await tg_logger.send_log(f"Ошибка при отправке поста для редактирования ID {post.id}:\n{e}")


@post_router.callback_query(F.data.startswith("prev:"), F.message.chat.id == settings.admin_chat_id)
async def album_prev_callback(callback: CallbackQuery):
    _, post_id, current_index = parse_callback_data(callback.data)
    if post_id is None or current_index is None:
        await callback.answer()
        return

    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            await callback.answer("Пост не найден.", show_alert=True)
            return

        media_list = await crud.get_media_by_post_id(session, post.id)
        if not media_list:
            await callback.answer("Нет медиа для поста.", show_alert=True)
            return

        new_index = (current_index - 1) % len(media_list)
        text = await make_post_text(post)
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="edit", index=new_index)
        next_item = media_list[new_index]
        media = InputMediaPhoto(media=next_item.telegram_file_id, caption=text) if next_item.media_type == "photo" else InputMediaVideo(media=next_item.telegram_file_id, caption=text)
        await callback.message.edit_media(media=media, reply_markup=keyboard)
        await callback.answer()


@post_router.callback_query(F.data.startswith("next:"), F.message.chat.id == settings.admin_chat_id)
async def album_next_callback(callback: CallbackQuery):
    _, post_id, current_index = parse_callback_data(callback.data)
    if post_id is None or current_index is None:
        await callback.answer()
        return

    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            await callback.answer("Пост не найден.", show_alert=True)
            return

        media_list = await crud.get_media_by_post_id(session, post.id)
        if not media_list:
            await callback.answer("Нет медиа для поста.", show_alert=True)
            return

        new_index = (current_index + 1) % len(media_list)
        text = await make_post_text(post)
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="edit", index=new_index)
        next_item = media_list[new_index]
        media = InputMediaPhoto(media=next_item.telegram_file_id, caption=text) if next_item.media_type == "photo" else InputMediaVideo(media=next_item.telegram_file_id, caption=text)
        await callback.message.edit_media(media=media, reply_markup=keyboard)
        await callback.answer()


@post_router.callback_query(F.data.startswith("noop:"), F.message.chat.id == settings.admin_chat_id)
async def noop_album_callback(callback: CallbackQuery):
    await callback.answer()


@post_router.callback_query(F.data.startswith("edit_text"), F.message.chat.id == settings.admin_chat_id)
async def edit_text_callback(callback: CallbackQuery, state: FSMContext):
    _, post_id, index = parse_callback_data(callback.data)
    
    # Get current post text to show user
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        current_text = extract_post_text_only(post.caption) if post else ""
    
    await state.update_data(
        post_id=post_id,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        index=index or 0
    )
    await callback.message.answer(f"Введите новый текст для поста:")
    await state.set_state(EditPostStates.waiting_for_text)


@post_router.message(EditPostStates.waiting_for_text, F.chat.id == settings.admin_chat_id)
async def process_new_text(message: Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")
    index = data.get("index", 0)
    new_text = message.text
    success = await edit_post_caption(post_id, new_text)

    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        media_list = await crud.get_media_by_post_id(session, post_id)
        text = await make_post_text(post)
        logger.info(f"Обновленный текст поста ID {post_id}:\n{text}")
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="edit", index=index)
        await bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=text,
            reply_markup=keyboard
        )

    if not success:
        await message.answer("Ошибка при обновлении текста поста. Ничего не произошло.")
    await state.clear()


@post_router.callback_query(F.data.startswith("ready_post"), F.message.chat.id == settings.admin_chat_id)
async def get_random_ready_post(callback: CallbackQuery):
    await asyncio.sleep(0.5)
    try:
        async with async_session() as session:
            posts = await crud.get_posts(session)
            ready_posts = [p for p in posts if p.status in (PostStatus.READY)]
            if not ready_posts:
                await callback.message.answer("Нет готовых постов.")
                return
            
            post = random.choice(ready_posts)
            media_list = await crud.get_media_by_post_id(session, post.id)
            text = await make_post_text(post)
            keyboard = await get_keyboard_for_post(post.id, media_list, mode="ready", index=0)
            await send_media_with_caption(media_list, callback.message, text, keyboard, index=0)
    except Exception as e:
        await tg_logger.send_log(f"Ошибка при отправке готового поста для проверки:\n{e}")


@post_router.message(Command("post_by_id"), F.chat.id == settings.admin_chat_id)
async def get_post_by_id(message: Message):
    post_id = message.text.split()[1]
    await asyncio.sleep(0.5)
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            await message.answer("Пост не найден.")
            return
        media_list = await crud.get_media_by_post_id(session, post.id)
        text = await make_post_text(post)
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="edit", index=0)
        await send_media_with_caption(media_list, message, text, keyboard, index=0)

async def get_edit_post_by_id(message: Message, post_id: int):
    await asyncio.sleep(0.5)
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            await message.answer("Пост не найден.")
            return
        media_list = await crud.get_media_by_post_id(session, post.id)
        text = await make_post_text(post)
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="edit", index=0)
        await send_media_with_caption(media_list, message, text, keyboard, index=0)

@post_router.callback_query(F.data.startswith("delete_post"), F.message.chat.id == settings.admin_chat_id)
async def delete_post_callback(callback: CallbackQuery):
    post_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        await crud.delete_post(session, post_id)
    await callback.message.edit_caption(caption=f"{callback.message.caption}\n\nПост успешно удален!",
                                        reply_markup=edit_post_only_keyboard(post_id))


@post_router.callback_query(F.data.startswith("not_ready"), F.message.chat.id == settings.admin_chat_id)
async def not_ready_callback(callback: CallbackQuery):
    post_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
        if not post:
            await callback.message.answer("Пост не найден.")
            return
        post.status = PostStatus.NEEDS_TEXT_EDIT
        session.add(post)
        await session.commit()
    await callback.message.edit_caption(caption=f"{callback.message.caption}\n\nПост снова требует редактирования текста!",
                                        reply_markup=post_edit_keyboard(post_id)
                                        )
    


@post_router.message(Command("delete_post"), F.chat.id == settings.admin_chat_id)
async def delete_post(message: Message):
    post_id = int(message.text.split()[1])
    async with async_session() as session:
        await crud.delete_post(session, post_id)
    await message.answer("Пост успешно удален!")

# выводит посты к которым не привязаны id медиа файлов для проверки, что удаление работает корректно
@post_router.message(Command("check_posts"), F.chat.id == settings.admin_chat_id)
async def check_posts(message: Message):
    ans = ""
    async with async_session() as session:
        posts = await crud.get_posts(session)
        for post in posts:
            media_list = await crud.get_media_by_post_id(session, post.id)
            if not media_list:
                ans += f"Пост ID {post.id} не имеет привязанных медиа файлов. Caption: {post.caption}\n"
    if ans == "":
        ans = "Всё в порядке"
    await message.answer(ans)

@post_router.message(Command("delete_posts"), F.chat.id == settings.admin_chat_id)
async def delete_posts(message: Message):
    post_ids = message.text.split()[1:]
    for post_id in post_ids:
        async with async_session() as session:
            await crud.delete_post(session, post_id)
    await message.answer("Посты успешно удалены!")


@post_router.callback_query(F.data.startswith("no_translate_post"), F.message.chat.id == settings.admin_chat_id)
async def get_media_posts(callback: CallbackQuery):
    await asyncio.sleep(0.5)  # Небольшая пауза, чтобы избежать проблем с API
    async with async_session() as session:
        posts = await crud.get_posts(session)
        edit_posts = [p for p in posts if p.status in (PostStatus.NEEDS_IMAGE_TRANSLATE, PostStatus.NEEDS_EDIT_AND_TRANSLATE)]
        if not edit_posts:
            await callback.message.answer("Нет постов для перевода изображений.")
            return
        
        post = random.choice(edit_posts)
        media_list = await crud.get_media_by_post_id(session, post.id)
        text = await make_post_text(post)
        keyboard = await get_keyboard_for_post(post.id, media_list, mode="translate", index=0)
        await send_media_with_caption(media_list, callback.message, text, keyboard, index=0)
