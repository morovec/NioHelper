# handlers/posts.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from database.db import async_session
from database import crud
from src.types.enums import PostStatus, Permission
from src.tg.keyboards.posts import post_status_keyboard, queue_keyboard, confirm_delete_keyboard

router = Router()


class AddPostStates(StatesGroup):
    waiting_for_media = State()
    waiting_for_text = State()
    waiting_for_status = State()


# ═══════════════════════════════════════════
#  ДОБАВЛЕНИЕ ПОСТА
# ═══════════════════════════════════════════

@router.message(Command("new_post"))
async def cmd_new_post(message: Message, state: FSMContext, admin=None, **kwargs):
    """Начать добавление нового поста."""
    if admin and not kwargs.get("is_owner"):
        return await message.answer("⛔ Нет права добавлять посты.")

    await state.clear()
    await state.set_state(AddPostStates.waiting_for_media)
    await state.update_data(media_list=[], text=None)

    await message.answer(
        "📎 <b>Отправьте медиа-файлы</b> (фото, видео).\n"
        "Можно отправить несколько — по одному или альбомом.\n\n"
        "Когда закончите — отправьте /done",
        parse_mode="HTML"
    )


@router.message(AddPostStates.waiting_for_media, F.photo)
async def receive_photo(message: Message, state: FSMContext, bot: Bot):
    """Получаем фото."""
    data = await state.get_data()
    media_list = data.get("media_list", [])

    # Берём самый большой размер фото
    photo = message.photo[-1]

    # Пересылаем в storage-канал
    storage_msg = await bot.send_photo(
        chat_id=settings.admin_chat_id,
        message_thread_id=settings.logs_thread_id,
        photo=photo.file_id,
    )

    media_list.append({
        "type": "photo",
        "file_id": photo.file_id,
        "file_unique_id": photo.file_unique_id,
        "storage_message_id": storage_msg.message_id
    })
    await state.update_data(media_list=media_list)
    await message.answer(f"✅ Фото добавлено ({len(media_list)} файл(ов))")


@router.message(AddPostStates.waiting_for_media, F.video)
async def receive_video(message: Message, state: FSMContext, bot: Bot):
    """Получаем видео."""
    data = await state.get_data()
    media_list = data.get("media_list", [])

    video = message.video

    storage_msg = await bot.send_video(
        chat_id=settings.admin_chat_id,
        message_thread_id=settings.logs_thread_id,
        video=video.file_id,
    )

    media_list.append({
        "type": "video",
        "file_id": video.file_id,
        "file_unique_id": video.file_unique_id,
        "storage_message_id": storage_msg.message_id
    })
    await state.update_data(media_list=media_list)
    await message.answer(f"✅ Видео добавлено ({len(media_list)} файл(ов))")


@router.message(AddPostStates.waiting_for_media, Command("done"))
async def media_done(message: Message, state: FSMContext):
    """Медиа загружены, переходим к тексту."""
    data = await state.get_data()
    if not data.get("media_list"):
        return await message.answer("❌ Вы не отправили ни одного файла.")

    await state.set_state(AddPostStates.waiting_for_text)
    await message.answer(
        "📝 Теперь отправьте <b>текст поста</b> (caption)."
    )


@router.message(AddPostStates.waiting_for_text, F.text)
async def receive_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await ask_status(message, state)


async def ask_status(message: Message, state: FSMContext):
    """Спрашиваем статус поста."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for status in PostStatus:
        builder.button(
            text=status.label,
            callback_data=f"new_post_status:{status.value}"
        )
    builder.adjust(1)

    await state.set_state(AddPostStates.waiting_for_status)
    await message.answer(
        "📋 Выберите <b>статус</b> поста:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(AddPostStates.waiting_for_status, F.data.startswith("new_post_status:"))
async def set_new_post_status(callback: CallbackQuery, state: FSMContext):
    """Сохраняем пост в БД."""
    status_value = callback.data.split(":")[1]
    status = PostStatus(status_value)

    data = await state.get_data()
    media_list = data["media_list"]
    caption = data.get("caption")

    async with async_session() as session:
        # Создаём пост
        post = await crud.create_post(
            session,
            caption=caption,
            status=status,
        )

        # Добавляем медиа
        for i, m in enumerate(media_list):
            await crud.add_media_to_post(
                session,
                post_id=post.id,
                media_type=m["type"],
                telegram_file_id=m["file_id"],
                telegram_file_unique_id=m.get("file_unique_id"),
                storage_message_id=m.get("storage_message_id"),
                sort_order=i
            )

    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Пост #{post.id} создан!</b>\n"
        f"Статус: {status.label}\n"
        f"Медиа: {len(media_list)} файл(ов)\n"
        f"Позиция в очереди: #{post.queue_position}",
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════
#  ПРОСМОТР ОЧЕРЕДИ
# ═══════════════════════════════════════════

@router.message(Command("queue"))
async def cmd_queue(message: Message):
    """Показать очередь постов."""
    async with async_session() as session:
        posts = await crud.get_posts(session)

    if not posts:
        return await message.answer("📭 Очередь пуста.")

    ready_count = sum(1 for p in posts if p.status == PostStatus.READY)
    total = len(posts)

    await message.answer(
        f"📋 <b>Очередь постов</b>\n"
        f"Всего: {total} | Готово к публикации: {ready_count}\n\n"
        f"Нажмите на пост для управления:",
        reply_markup=queue_keyboard(posts)
    )


@router.callback_query(F.data.startswith("view_post:"))
async def cb_view_post(callback: CallbackQuery):
    """Просмотр конкретного поста."""
    post_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        post = await crud.get_post(session, post_id)

    if not post:
        return await callback.answer("❌ Пост не найден", show_alert=True)

    media_info = "\n".join(
        f"  {i+1}. {m.media_type} (file_id: ...{m.telegram_file_id[-10:]})"
        for i, m in enumerate(post.media)
    )

    text = (
        f"📄 <b>Пост #{post.id}</b>\n"
        f"Статус: {post.status.label}\n"
        f"Медиа ({len(post.media)}):\n{media_info}\n\n"
        f"Текст: {(post.caption or 'Без текста')[:200]}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=post_status_keyboard(post_id)
    )


# ═══════════════════════════════════════════
#  СМЕНА СТАТУСА / УДАЛЕНИЕ
# ═══════════════════════════════════════════

@router.callback_query(F.data.startswith("set_status:"))
async def cb_set_status(callback: CallbackQuery):
    """Смена статуса поста."""
    parts = callback.data.split(":")
    post_id = int(parts[1])
    new_status = PostStatus(parts[2])

    async with async_session() as session:
        await crud.update_post_status(session, post_id, new_status)

    await callback.answer(f"Статус: {new_status.label}")

    # Обновляем сообщение
    async with async_session() as session:
        post = await crud.get_post(session, post_id)
    if post:
        media_info = "\n".join(
            f"  {i+1}. {m.media_type}"
            for i, m in enumerate(post.media)
        )
        await callback.message.edit_text(
            f"📄 <b>Пост #{post.id}</b>\n"
            f"Статус: {post.status.label}\n"
            f"Позиция: #{post.queue_position}\n"
            f"Медиа ({len(post.media)}):\n{media_info}\n\n"
            f"Текст: {(post.caption or 'Без текста')[:200]}",
            reply_markup=post_status_keyboard(post_id)
        )


@router.callback_query(F.data.startswith("delete_post:"))
async def cb_delete_post(callback: CallbackQuery):
    post_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"🗑 Удалить пост #{post_id}?",
        reply_markup=confirm_delete_keyboard(post_id)
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def cb_confirm_delete(callback: CallbackQuery):
    post_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        await crud.delete_post(session, post_id)
    await callback.message.edit_text(f"✅ Пост #{post_id} удалён.")


@router.callback_query(F.data.startswith("cancel_delete:"))
async def cb_cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Удаление отменено.")


# ═══════════════════════════════════════════
#  РЕДАКТИРОВАНИЕ ТЕКСТА
# ═══════════════════════════════════════════

class EditTextStates(StatesGroup):
    waiting_for_new_text = State()


@router.message(Command("edit_text"))
async def cmd_edit_text(message: Message, state: FSMContext, **kwargs):
    """/edit_text 5 — редактировать текст поста #5"""
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Использование: /edit_text <post_id>")

    post_id = int(args[1])
    await state.set_state(EditTextStates.waiting_for_new_text)
    await state.update_data(edit_post_id=post_id)
    await message.answer(f"📝 Отправьте новый текст для поста #{post_id}:")


@router.message(EditTextStates.waiting_for_new_text, F.text)
async def receive_new_text(message: Message, state: FSMContext):
    data = await state.get_data()
    post_id = data["edit_post_id"]

    old_caption = await crud.get_post(post_id=post_id)

    async with async_session() as session:
        updated = await crud.update_post_text(session, post_id, message.text)

    await state.clear()
    if updated:
        await message.answer(f"✅ Текст поста #{post_id} обновлён.")
    else:
        await message.answer(f"❌ Пост #{post_id} не найден.")