from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import settings

from src.database import crud
from src.database.db import async_session
from src.types.enums import PostStatus

stats_router = Router()

async def get_posts_amount():
    async with async_session() as session:
        posts = await crud.get_posts(session)

    if not posts:
        return 0, 0

    ready_count = sum(1 for p in posts if p.status == PostStatus.READY)
    total = len(posts)

    return total, ready_count


async def get_without_translate():
    async with async_session() as session:
        posts = await crud.get_posts(session)

    if not posts:
        return 0

    without_translate_count = sum(1 for p in posts if p.status == PostStatus.NEEDS_IMAGE_TRANSLATE or p.status == PostStatus.NEEDS_EDIT_AND_TRANSLATE)

    return without_translate_count

async def get_status():
    total, ready_count = await get_posts_amount()

    text = f"""
    <b>Количество:</b>
        Отложенные посты: <b>{total}</b>
        Готовые к публикации: <b>{ready_count}</b>
        Без текста: <b>{total - ready_count}</b>
        Без перевода: <b>{await get_without_translate()}</b>
    """

    return text

@stats_router.message(Command("status"), F.chat.id == settings.admin_chat_id)
async def group_stats(message: Message) -> None:
    text = await get_status()
    await message.answer(text=text)