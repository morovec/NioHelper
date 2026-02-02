from config import settings, tg_bot as tg

from aiogram.types import FSInputFile


class PostingNotify:
    def __init__(self):
        self.message = None
        self.message_id = None
        self.count = 0

    async def msg_to_translation(self, paths: list[str]):
        for path in paths:
            await tg.send_document(chat_id=settings.admin_chat_id,
                                   document=FSInputFile(path),
                                   message_thread_id=settings.telegram.translation_thread_id)

    async def msg_to_posting(self, text):
        self.message = text
        self.count = 0
        self.message_id = (await tg.send_message(
            chat_id=settings.admin_chat_id,
            text=text,
            message_thread_id=settings.telegram.posting_thread_id)
            ).message_id

    async def edit_message(self, text):
        self.message = text
        await tg.edit_message_text(
              chat_id=settings.telegram.posting_thread_id,
              text=text, 
              message_id=self.message_id
              )
            
    async def add_success_post(self, post_msg):
        self.count += 1
        msg = f"\n{post_msg} {self.count}"
        if "Ошибки" in self.message:
            split_message = self.message.split("\n\n")
            self.message = split_message[0] + msg + "\n\n" + split_message[1]
        else:
            self.message += msg
        await tg.edit_message_text(
              chat_id=settings.admin_chat_id,
              text=self.message, 
              message_id=self.message_id
              )
    
    async def add_error_post(self, post):
        if "Ошибки" not in self.message:
            self.message = self.message + "\n\nОшибки в постах:"
        self.message += f"\n{post}"
        await tg.edit_message_text(
              chat_id=settings.admin_chat_id,
              text=self.message, 
              message_id=self.message_id
              )
        
posting_notify = PostingNotify()

class TelegramLogger:
     async def send_log(self, text):
        await tg.send_message(
            chat_id=settings.admin_chat_id,
            message_thread_id=settings.logs_thread_id,
            text=text
            )

tg_logger = TelegramLogger()