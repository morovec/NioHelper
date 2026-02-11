import yaml
import os
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from aiogram import Bot as TGBot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from vkbottle.bot import Bot as VKBot
from vkbottle.user import User as VKUser

from aiohttp import BasicAuth
from aiogram.client.session.aiohttp import AiohttpSession


@dataclass
class TelegramConfig:
    token: str
    group_id: str
    admin_chat_id: int
    events_thread_id: int
    posting_thread_id: int
    logs_thread_id: int
    translation_thread_id: int
    owner_id: Optional[int] = None

@dataclass
class VKConfig:
    bot_token: str
    user_token: str
    group_id: int
    owner_id: int

@dataclass
class LoggingConfig:
    level: str
    file: str
    rotation: str

@dataclass
class RetryConfig:
    max_attempts: int
    delay_seconds: int

@dataclass
class ProxyConfig:
    proxy: dict

@dataclass
class FuraffinityConfig:
    cookies: dict

@dataclass
class Settings:
    telegram: TelegramConfig
    vk: VKConfig
    logging: LoggingConfig
    retries: RetryConfig
    proxy: ProxyConfig
    furaffinity: FuraffinityConfig
    
    @property
    def owner_id(self) -> Optional[int]:
        return self.telegram.owner_id
    
    @property
    def admin_chat_id(self) -> Optional[int]:
        return self.telegram.admin_chat_id
    
    @property
    def logs_thread_id(self) -> Optional[int]:
        return self.telegram.logs_thread_id
    
    @property
    def proxy_get(self) -> Optional[dict]:
        return self.proxy.proxy

    @property
    def fa_cookies_get(self) -> Optional[dict]:
        return self.furaffinity.cookies
    
    @property
    def posting_thread_id(self) -> Optional[dict]:
        return self.telegram.posting_thread_id


def load_settings(path: str = "config.yaml") -> Settings:
    """
    Loads YAML and maps it into typed Dataclasses.
    """
    if not os.path.exists(path):
        # Return None or raise error. 
        # For this setup, we raise so the user knows they missed the file.
        raise FileNotFoundError(f"Missing {path}! Copy config.example.yaml to config.yaml first.")
        
    with open(path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)
    
    # Validation: Ensure sections exist before unpacking
    return Settings(
        telegram=TelegramConfig(**raw_data['telegram']),
        vk=VKConfig(**raw_data['vk']),
        logging=LoggingConfig(**raw_data['logging']),
        retries=RetryConfig(**raw_data['retries']),
        proxy=ProxyConfig(raw_data['proxy']),
        furaffinity=FuraffinityConfig(raw_data['furaffinity']),
    )

# Global settings instance
try:
    settings = load_settings()

    session = AiohttpSession(proxy=settings.proxy_get["https"])

    vk_user = VKUser(token=settings.vk.user_token)
    vk_bot = vk_bot = VKBot(token=settings.vk.bot_token)
        
    tg_bot = TGBot(token=settings.telegram.token,
                   default=DefaultBotProperties(parse_mode=ParseMode.HTML),
                   session=session)
except Exception as ex:
    # Fallback for initialization or when file is missing (e.g. during first setup)
    logger.critical(ex)
    settings = None
