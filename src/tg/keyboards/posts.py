# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lxml import builder

from src.types.enums import PostStatus


def edit_queue_keyboard(post: list) -> InlineKeyboardMarkup:
    """Клавиатура очереди постов."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"<-",
        callback_data=f"back:{post.id}"
    )
    builder.button(
        text=f"✏️ Редактировать",
        callback_data=f"edit:{post.id}"
    )
    builder.button(
        text=f"->",
        callback_data=f"next:{post.id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_keyboard(post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, удалить",
                callback_data=f"confirm_delete:{post_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"cancel_delete:{post_id}"
            ),
        ]
    ])