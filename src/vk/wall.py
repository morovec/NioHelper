from vkbottle.bot import BotLabeler
from vkbottle import GroupEventType, GroupTypes
from vkbottle_types.objects import WallWallpostAttachment, WallWallpostAttachmentType

from typing import Optional

from config import settings, tg_bot as tg, vk_user as vk
from src.tg.notify import tg_logger
from src.handlers.utils import vk_text_to_tg
from src.vk.media import media_downloader

from aiogram.types import InputMediaPhoto, InputMediaAnimation, URLInputFile, InputMediaDocument

wall_labeler = BotLabeler()

def get_copyright_from_caption(caption: str) -> str:
    return caption.split()[-1]

def author_copyright(text: str, copyright_url: str, author: str) -> str:
    if not text: return None
    text = text.replace(f"Автор: {author}",
                        f'Автор: <a href="{copyright_url}">{author}</a>')
    return text

async def repost_post(text: str, attachments: list[WallWallpostAttachment]) -> Optional[str]:
    text = vk_text_to_tg(text)
    await tg_logger.send_log("Пытаюсь сделать репост...")
    attachments_amount = len(attachments)

    tg_attachments = []
    author = ""
    copyright_url = ""
    if "Автор: " in text:
        author = " ".join(text.split("\n\n")[-2].split()[1:])
    
    for attachment in attachments:
        if attachment.type == WallWallpostAttachmentType.PHOTO:
            if not copyright_url:
                copyright_url = get_copyright_from_caption(attachment.photo.text)
            text = author_copyright(text, copyright_url, author)

            photo_url = attachment.photo.sizes[-1].url
            photo = URLInputFile(url=photo_url, filename="media.png")

            if attachments_amount == 0:
                try:
                    await tg.send_photo(chat_id=settings.telegram.group_id,
                                        photo=photo,
                                        caption=text)
                except Exception as ex:
                    await tg_logger.send_log(f"Hе получилось сделать репост: {ex}")
            else:
                tg_attachments.append(InputMediaPhoto(media=photo, caption=text))
                
        elif attachment.type == WallWallpostAttachmentType.VIDEO:
            if not copyright_url:
                copyright_url = get_copyright_from_caption(attachment.video.description)
            text = author_copyright(text, copyright_url, author)
            video_data = media_downloader.video(attachment.video)

            video = URLInputFile(url=video_data["url"],
                                 filename="video.mp4",
                                 headers=video_data["headers"])

            if attachments_amount == 1:
                try:
                    await tg.send_animation(chat_id=settings.telegram.group_id,
                                            animation=video,
                                            caption=text)
                except Exception as ex:
                    await tg_logger.send_log(f"Hе получилось сделать репост: {ex}")
            else:
                tg_attachments.append(InputMediaAnimation(media=video,
                                                          caption=text))
                

        elif attachment.type == WallWallpostAttachmentType.DOC:
            if not copyright_url:
                copyright_url = get_copyright_from_caption(attachment.doc.title)
            text = author_copyright(text, copyright_url, author)

            doc_url = attachment.doc.url

            doc = URLInputFile(url=doc_url,
                               filename="media.gif")

            if attachments_amount == 1:
                try:
                    await tg.send_document(chat_id=settings.telegram.group_id,
                                           document=doc,
                                           caption=text)
                except Exception as ex:
                    await tg_logger.send_log(f"Hе получилось сделать репост: {ex}")
            else:
                tg_attachments.append(InputMediaDocument(media=doc,
                                                         caption=text))
        text = None

    if attachments_amount > 1:
        try:
            await tg.send_media_group(chat_id=settings.telegram.group_id,
                                      media=tg_attachments)
            await tg_logger.send_log(f"Успешный репост!")
        except Exception as ex:
            await tg_logger.send_log(f"Ошибка при отправке поста в тг: {ex}")

    if copyright_url:
        return f'Оригинал:\n{copyright_url}'
        

@wall_labeler.raw_event(GroupEventType.WALL_POST_NEW, GroupTypes.WallPostNew)
async def wall_bridge(event: GroupTypes.WallPostNew):
    if event.type == "suggest" or event.object.donut.is_donut:
        return 0
    
    comment_msg = await repost_post(text=event.object.text,
                                    attachments=event.object.attachments)
    if comment_msg:
        await vk.api.wall.create_comment(owner_id=-settings.vk.group_id,
                                        post_id=event.object.id,
                                        message=comment_msg,
                                        from_group=settings.vk.group_id)
        await tg_logger.send_log("Отправил оригинал под пост!")