# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.types.enums import PostStatus

def post_edit_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=f"edit_text:{post_id}"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"get_random_edit_post")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Скрыть", callback_data=f"hide")
    )
    return builder.as_markup()

def post_edit_keyboard_without_delete(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=f"edit_text:{post_id}"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"get_random_edit_post")
    )
    builder.row(
        InlineKeyboardButton(text="Скрыть", callback_data=f"hide")
    )
    return builder.as_markup()