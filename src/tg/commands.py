from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import settings

command_router = Router(name=__name__)

@command_router.message(Command("check_thread"), F.chat.id == settings.admin_chat_id)
async def check_threads(message: Message) -> None:
    text = f"chat_id: {message.chat.id}\nthread_id: {message.message_thread_id}"
    await message.answer(text=text)

