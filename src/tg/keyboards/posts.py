# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


def post_edit_keyboard(post_id: int, index: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    edit_callback = f"edit_text:{post_id}:{index}" if index else f"edit_text:{post_id}"
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=edit_callback, style="success"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"no_text_post", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}", style="danger")
    )
    return builder.as_markup()


def post_album_edit_keyboard(post_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    edit_callback = f"edit_text:{post_id}:{index}" if index else f"edit_text:{post_id}"
    builder.row(
        InlineKeyboardButton(text="Редактировать текст", callback_data=edit_callback, style="success"),
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"no_text_post", style="primary")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}", style="danger")
    )
    builder.row(
        InlineKeyboardButton(text=" <- ", callback_data=f"prev:{post_id}:{index}", style="primary"),
        InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data=f"noop:{post_id}:{index}"),
        InlineKeyboardButton(text=" -> ", callback_data=f"next:{post_id}:{index}", style="primary")
    )
    return builder.as_markup()


def post_edit_media_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"no_translate_post", style="success")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}", style="danger")
    )
    return builder.as_markup()


def post_album_edit_media_keyboard(post_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"no_translate_post", style="success")
    )
    builder.row(
        InlineKeyboardButton(text="Удалить пост", callback_data=f"delete_post:{post_id}", style="danger")
    )
    builder.row(
        InlineKeyboardButton(text=" <- ", callback_data=f"prev:{post_id}:{index}", style="primary"),
        InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data=f"noop:{post_id}:{index}"),
        InlineKeyboardButton(text=" -> ", callback_data=f"next:{post_id}:{index}", style="primary")
    )
    return builder.as_markup()


def post_album_ready_keyboard(post_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Не готов", callback_data=f"not_ready:{post_id}", style="primary"),
        InlineKeyboardButton(text="Удалить", callback_data=f"delete_post:{post_id}", style="danger")
    )
    builder.row(
        InlineKeyboardButton(text=" <- ", callback_data=f"prev:{post_id}:{index}", style="primary"),
        InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data=f"noop:{post_id}:{index}"),
        InlineKeyboardButton(text=" -> ", callback_data=f"next:{post_id}:{index}", style="primary")
    )
    return builder.as_markup()

def edit_post_only_keyboard(post_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Взять другой пост", callback_data=f"no_text_post", style="success"),
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