from loguru import logger

from config import settings, vk_user as vk, tg_bot as tg
from src.tg.keyboards import get_comment_del_kb, get_comment_kb
from src.types import CommentData

from aiogram.types import CallbackQuery
from aiogram import Router, F

comments_router = Router(name=__name__)

def get_data_from_callback(callback: CallbackQuery) -> CommentData:
    urls = [entity for entity in callback.message.entities if entity.type == "text_link"]
    url = urls[0].url
    comment_id = url.split("reply=")[-1]
    return CommentData(comment_id, url)

@comments_router.callback_query(F.data == "comment_restore")
async def comment_restore(callback: CallbackQuery) -> None:
    name = callback.from_user.first_name
    comment_data = get_data_from_callback(callback=callback)
    text = ("\n\n".join(callback.message.text.split("\n\n")[:-1]) + "\n\n" +
            f'<a href="{comment_data.url}">ВОССТАНОВЛЕН {name}</a>')
    keyboard = get_comment_kb()
    await vk.api.wall.restore_comment(owner_id=-settings.vk.group_id,
                                      comment_id=comment_data.id)
    await tg.edit_message_text(text=text,
                               chat_id=settings.admin_chat_id,
                               message_id=callback.message.message_id,
                               reply_markup=keyboard)

@comments_router.callback_query(F.data == "comment_delete")
async def comment_delete(callback: CallbackQuery) -> None:
    name = callback.from_user.first_name
    message_id = callback.message.message_id

    comment_data = get_data_from_callback(callback=callback)
    await vk.api.wall.delete_comment(owner_id=-settings.vk.group_id,
                                     comment_id=comment_data.id)
    raw_text = callback.message.text
    if f"ВОССТАНОВЛЕН " in raw_text:
        raw_text = "\n\n".join(raw_text.split("\n\n")[:-1])
    text = (raw_text + "\n\n" +
            f'<a href="{comment_data.url}">УДАЛЕН {name}</a>')
    keyboard = get_comment_del_kb()
    await tg.edit_message_text(text=text,
                               chat_id=settings.admin_chat_id,
                               message_id=message_id,
                               reply_markup=keyboard)