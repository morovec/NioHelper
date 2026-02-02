import requests
from typing import Optional, Dict, Any
from config import settings
from pathlib import Path

from loguru import logger

def file_save_from_url(
        path: str, 
        url: str, 
        proxy_use: bool = False, 
        data: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, Any]] = None) -> None:
    """
    Сохраняет файл по ссылке.

    :param path: Путь для сохранения файла.
    :param url: Ссылка на файл.
    :param proxy_use: Использовать прокси (по умолчанию False).
    :param data: Данные для GET запроса (опционально).
    :param headers: Заголовки для GET запроса (опционально).
    :return: None
    """

    try:
        response = requests.get(
            url,
            proxies=settings.proxy_get if proxy_use else None,
            data=data,
            headers=headers
        )
        response.raise_for_status()  # Проверка на ошибки HTTP

        with open(path, "wb") as out_file:
            out_file.write(response.content)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
    except IOError as e:
        logger.error(f"Ошибка при сохранении файла: {e}")

def file_save(path: str | Path, file: bytes) -> None:
    """
    Сохраняет файл на устройство.

    :param path: Путь для сохранения файла.
    :param file: Файл в виде байтов.
    :return: None
    """

    try:
        with open(str(path), "wb") as out_file:
            out_file.write(file)
    except IOError as e:
        logger.error(f"Ошибка при сохранении файла: {e}")

def file_open(path: str | Path):
    """
    Открывает файл с устройства.

    :param path: Путь к файлу.
    :return: Файловый объект.
    """
    try:
        return open(str(path), 'rb')
    except IOError as e:
        logger.error(f"Ошибка при открытии файла: {e}")
        return None