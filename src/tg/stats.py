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
        return ("📭 Очередь пуста.")

    ready_count = sum(1 for p in posts if p.status == PostStatus.READY)
    total = len(posts)

    return total, ready_count

async def get_stats():
    total, ready_count = await get_posts_amount()

    text = f"""
    <b>Количество:</b>
        Отложенные посты: <b>{total}</b>
        Готовые к публикации: <b>{ready_count}</b>
    """

    return text

@stats_router.message(Command("stats"), F.chat.id == settings.admin_chat_id)
async def group_stats(message: Message) -> None:
    text = await get_stats()
    await message.answer(text=text)