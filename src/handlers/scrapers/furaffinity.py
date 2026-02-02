from bs4 import BeautifulSoup
import requests
from loguru import logger
from config import settings
from src.handlers import file_save_from_url
from src.resources.datas import path_to_media

from src.types.post import PostParsed
def get_fa_post(url: str) -> PostParsed:
    """
    Получает информацию из ссылки поста.

    :param url: Ссылка.
    :return: Словарь с информаций.
    """
    logger.debug("Furaffinity post scraping")
    try:
        response = requests.get(url, cookies=settings.fa_cookies_get, proxies=settings.proxy_get).text

        soup = BeautifulSoup(response, 'lxml')
        text = soup.find("meta", property="og:title", content=True).attrs["content"].split(" by ")
        author = text[-1]
        link = "https:" + soup.find("div", {"class": "download"}).find("a")["href"]
        
        if ".gif" in link:
            path = f"{path_to_media}.gif"
        elif ".mp4" in link:
            path = f"{path_to_media}.mp4"
        else:
            path = f"{path_to_media}.png"

        file_save_from_url(path=path,
                           url=link,
                           proxy_use=True)

        fa_data = PostParsed(media_paths=[path],
                             author=author)

        logger.debug(f"Returning furaffinity data scraped:\n{fa_data}")
        return fa_data

    except IndexError:
        logger.error(f"Cookies need to be updated!")
        raise Exception

    except Exception as x:
        logger.error(x)