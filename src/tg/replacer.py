from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from config import settings, tg_bot as tg
from database import crud
from src.tg.notify import tg_logger

from src.resources import messages, path_to_replacer

import traceback

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

    async def compare_imgs(self, old_list: list[str]) -> list[str]:
        new_list = await self.create_new_list(len(old_list))
        res = []
        for i, img in enumerate(new_list):
            if img:
                res.append(img)
            else:
                res.append(old_list[i])
        self.imgs = []
        return res
    
    async def create_new_list(self, amount: int) -> list[str]:
        new_list = [""] * amount
        for img in self.imgs:
            new_list[img.position-1] = img.media_id
        return new_list

    def add_new_img(self, img: ImgReplace):
        self.imgs.append(img)

    def clear_list(self):
        self.imgs = []

media_replacer = MediaReplacer()

async def replace_images(post_id: str) -> None:
    try:
        # Получаем текущие вложения
        attachments = await crud.get_media_by_post_id(post_id=post_id)

        if not attachments:
            await tg_logger.send_log("В посте нет изображений")
            return False
        
        new_attachments = await media_replacer.compare_imgs(attachments)

        # Обновляем вложения в базе данных
        await crud.update_post_media(post_id=post_id, new_media_ids=new_attachments)
        
        return True
            
    except:
        await tg_logger.send_log(f"Ошибка при замене изображений: {traceback.format_exc()}")
        return 
    
@replace_router.message(Command("add_img"), F.chat.id == settings.admin_chat_id)
async def add_img(callback: CallbackQuery):
    position = callback.message.caption

    path = path_to_replacer + position + ".png"

    try:
        file_id = callback.message.document.file_id
        file = await tg.get_file(file_id)

        await tg.download_file(file.file_path, path)

    except Exception as ex:
        await tg_logger.send_log(f"Не скачалась фоточка {ex}")
        return


    new_img = ImgReplace(media_path=path, position=int(position))
    media_replacer.add_new_img(new_img)
    await callback.message.answer("Добавил фото!")

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
            await message.answer("Укажите ID поста")
            return
        
        post_id = parts[1]
        
        if await replace_images(post_id):
            await message.answer("Замена изображения завершена")
        
    except:
        await tg_logger.send_log(f"Ошибка: {traceback.format_exc()}")