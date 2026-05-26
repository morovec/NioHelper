# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


def post_edit_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=f"edit_text:{post_id}", style="success"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"no_text_post", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}", style="danger")
    )
    return builder.as_markup()

def post_ready_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Не готов", callback_data=f"not_ready:{post_id}", style="primary"),
        InlineKeyboardButton(text="Удалить", callback_data=f"delete_post:{post_id}", style="danger")
    )
    return builder.as_markup()


def post_translate_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Изменить перевод", callback_data=f"edit_translate:{post_id}", style="success")
    )
    return builder.as_markup()


def post_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пост без текста", callback_data="no_text_post", style="danger")
    )
    builder.row(
        InlineKeyboardButton(text="Пост без перевода", callback_data="no_translate_post", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Готовый пост", callback_data="ready_post", style="success")
    )
    return builder.as_markup(resize_keyboard=True)