# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.types.enums import PostStatus, Permission


def post_status_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для смены статуса поста."""
    builder = InlineKeyboardBuilder()
    for status in PostStatus:
        builder.button(
            text=status.label,
            callback_data=f"set_status:{post_id}:{status.value}"
        )
    builder.button(text="🗑 Удалить пост", callback_data=f"delete_post:{post_id}")
    builder.adjust(1)
    return builder.as_markup()


def queue_keyboard(posts: list) -> InlineKeyboardMarkup:
    """Клавиатура очереди постов."""
    builder = InlineKeyboardBuilder()
    for post in posts[:20]:  # Максимум 20 кнопок
        status_emoji = {
            PostStatus.READY: "✅",
            PostStatus.NEEDS_TEXT_EDIT: "✏️",
            PostStatus.NEEDS_IMAGE_TRANSLATE: "🖼",
            PostStatus.NEEDS_EDIT_AND_TRANSLATE: "🔄",
        }.get(post.status, "❓")

        media_count = len(post.media)
        text_preview = (post.text or "Без текста")[:30]

        builder.button(
            text=f"{status_emoji} #{post.id} | 📎{media_count} | {text_preview}",
            callback_data=f"view_post:{post.id}"
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