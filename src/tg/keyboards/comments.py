from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardButton, InlineKeyboardMarkup)

def get_comment_kb():
    comment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить", callback_data="comment_delete")]
    ])

    return comment_keyboard


def get_comment_del_kb():
    comment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Восстановить", callback_data="comment_restore")]
    ])

    return comment_keyboard