from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import settings, vk_user as vk, tg_bot as tg
from src.tg.notify import tg_logger

from src.resources import messages, path_to_replacer
from src.handlers import file_save_from_url

import traceback

from src.vk.media import media_uploader
from vkbottle_types.codegen.objects import WallWallpostFull

from src.types import ImgReplace

replace_router = Router(name=__name__)

class MediaReplacer:
    def __init__(self):
        self.imgs: list[ImgReplace] = []

    def status(self) -> str:
        text = f"Всего замен: {len(self.imgs)}\nСлоты замены: "
        for img in self.imgs:
            text += str(img.position)
        return text

    async def compare_imgs(self, old_list: list[str], copyright_url: str) -> list[str]:
        new_list = await self.create_new_list(len(old_list), copyright_url)
        res = []
        for i, img in enumerate(new_list):
            if img:
                res.append(img)
            else:
                res.append(old_list[i])
        self.imgs = []
        return res
    
    async def create_new_list(self, amount: int, post_url: str) -> list[str]:
        new_list = [""] * amount
        for img in self.imgs:
            vk_attachment = await media_uploader.upload_media([img.media_path], post_url)
            new_list[img.position-1] = vk_attachment[0]
        
        return new_list

    def add_new_img(self, img: ImgReplace):
        self.imgs.append(img)

    def clear_list(self):
        self.imgs = []

media_replacer = MediaReplacer()

async def replace_images(post_id: str) -> None:
    try:
        # Получаем текущие вложения
        posts = await vk.api.wall.get_by_id(posts=post_id)
        
        post = posts.items[0]
        attachments = post.attachments

        if not attachments:
            await tg_logger.send_log("В посте нет изображений")
            return False
        
        old_imgs = []
        copyright_url = ""
        for i, attachment in enumerate(attachments):
            photo = attachment.photo
            attach = f"photo{photo.owner_id}_{photo.id}"
            if photo.access_key: attach += f"_{photo.access_key}"
            old_imgs.append(attach)

            if not copyright_url:
                copyright_url = attachment.photo.text.split()[-1]

        new_attachments = await media_replacer.compare_imgs(old_imgs, copyright_url)
        await vk.api.wall.edit(post_id=post.id,
                               owner_id=post.owner_id,
                               attachments=new_attachments,
                               message=post.text,
                               publish_date=post.date)
        return True
            
    except:
        await tg_logger.send_log(f"Ошибка при замене изображений: {traceback.format_exc()}")
        return 
    
@replace_router.message(Command("add_img"), F.chat.id == settings.admin_chat_id)
async def add_img(message: Message):
    parts = message.caption.split()

    if len(parts) < 2:
        position = "1"
    else:
        position = parts[1]

    path = path_to_replacer + position + ".png"

    try:
        file_id = message.document.file_id
        file = await tg.get_file(file_id)

        await tg.download_file(file.file_path, path)

    except Exception as ex:
        await tg_logger.send_log(f"Не скачалась фоточка {ex}")
        return


    new_img = ImgReplace(media_path=path, position=int(position))
    media_replacer.add_new_img(new_img)
    await message.answer("Добавил фото!")

@replace_router.message(Command("clear_imgs"), F.chat.id == settings.admin_chat_id)
async def clear_imgs(message: Message):
    media_replacer.clear_list()
    await message.answer("Очищено!")

@replace_router.message(Command("replace_status"), F.chat.id == settings.admin_chat_id)
async def replace_status(message: Message):
    status = media_replacer.status()
    await message.answer(f"Статус замены:\n{status}")

@replace_router.message(Command("replace_remind"), F.chat.id == settings.admin_chat_id)
async def replace_remind(message: Message):
    await message.answer(messages.replace_remind)

@replace_router.message(Command("replace"), F.chat.id == settings.admin_chat_id)
async def handle_replace(message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Укажите url поста")
            return
        
        post_id = parts[1].split("wall")[1]
        
        if await replace_images(post_id):
            await message.answer("Замена изображения завершена")
        
    except:
        await tg_logger.send_log(f"Ошибка: {traceback.format_exc()}")