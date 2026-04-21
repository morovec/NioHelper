# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.types.enums import PostStatus

def post_edit_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=f"edit_text:{post_id}", style="success"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"get_random_edit_post", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Готово", callback_data=f"ready_for_posting:{post_id}", style="success")
    )
    builder.row(
        InlineKeyboardButton(text="Скрыть", callback_data=f"hide")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}", style="danger")
    )
    return builder.as_markup()

def post_edit_keyboard_without_delete(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=f"edit_text:{post_id}", style="success"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"get_random_edit_post", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Скрыть", callback_data=f"hide")
    )
    return builder.as_markup()

def post_ready_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Не готов", callback_data=f"not_ready:{post_id}", style="primary"),
        InlineKeyboardButton(text="Удалить", callback_data=f"delete_post:{post_id}", style="danger")
    )
    builder.row(
        InlineKeyboardButton(text="Скрыть", callback_data=f"hide")
    )
    return builder.as_markup()


def post_translate_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Изменить перевод", callback_data=f"edit_translate:{post_id}", style="success")
    )

    builder.row(
        InlineKeyboardButton(text="Скрыть", callback_data=f"hide")
    )
    return builder.as_markup()