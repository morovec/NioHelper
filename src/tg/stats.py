from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import settings, vk_user as vk

stats_router = Router()

async def get_postponed_posts():
    posts_amount = (await vk.api.wall.get(count=100,
                                          domain=f"club{settings.vk.group_id}",
                                          filter="postponed")).count
    return posts_amount

async def get_stats():
    posts_amount = await get_postponed_posts()
    subscribers_amount = (await vk.api.groups.get_members(group_id=settings.vk.group_id,
                                                          count=1)).count

    text = f"""
    <b>Количество:</b>
        Отложенные посты: <b>{posts_amount}</b>
        Подписчики: <b>{subscribers_amount}</b>
    """

    return text

@stats_router.message(Command("stats"), F.chat.id == settings.admin_chat_id)
async def group_stats(message: Message) -> None:
    text = await get_stats()
    await message.answer(text=text)