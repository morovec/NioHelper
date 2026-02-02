from vkbottle.bot import BotLabeler
from vkbottle import GroupEventType, GroupTypes

from src.tg.keyboards import get_comment_kb

from config import settings, vk_user as vk, tg_bot as tg

from loguru import logger

comments_labeler = BotLabeler()

@comments_labeler.raw_event(GroupEventType.WALL_REPLY_NEW, GroupTypes.WallReplyNew)
async def new_comment(event: GroupTypes.WallReplyNew):
    from_id = event.object.from_id
    if from_id > 0:
        user_data = (await vk.api.users.get(user_ids=from_id))[0]
        logger.debug(user_data)
        name = f"{user_data.first_name} {user_data.last_name}"
    else:
        group_data = await vk.api.groups.get_by_id(group_id=-from_id)
        name = group_data.groups[0].name

    if event.object.text:
        link = f'https://vk.com/wall{event.object.owner_id}_{event.object.post_id}'

        text = (f'Комментарий под постом!\n\n{name}\n'
                f'<a href="{link}?reply={event.object.id}">{event.object.text}</a>')

        keyboard = get_comment_kb()

        await tg.send_message(chat_id=settings.admin_chat_id,
                              message_thread_id=settings.telegram.events_thread_id,
                              text=text,
                              reply_markup=keyboard)