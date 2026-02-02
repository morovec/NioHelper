from .furaffinity import get_fa_post
from .reddit import reddit_downloader
from .twitter import get_tweet
from .vk import get_vk_post

from src.types.post import PostParsed

from urllib.parse import urlparse

from loguru import logger

twitter_instances = [
    "xcancel.com",
    "nitter.poast.org",
    "nitter.privacyredirect.com",
    "lightbrd.com",
    "nitter.space",
    "nitter.net",
    "nitter.tiekoetter.com",
    "nuku.trabun.org",
    "nitter.catsarch.com",
    "x.com",
    "twitter.com"
]

reddit_instances = [
    "reddit.com",
    "old.reddit.com"
]

vk_instances = [
    "vk.com",
    "vk.ru"
]

async def get_post_from_url(url: str) -> PostParsed:
    logger.debug(f"Parsing url: {url}")
    parsed = urlparse(url)
    domain = parsed.hostname.lower()
    domain = domain.replace("www.", "")

    if domain == "furaffinity.net":
        return get_fa_post(url)

    elif domain in reddit_instances:
        url = url.replace(domain, "reddit.com")
        return await reddit_downloader.fetch_post(url)

    elif domain in twitter_instances:
        url = url.replace(domain, "api.fxtwitter.com")
        return get_tweet(url)
    
    elif domain in vk_instances:
        url = url.replace(domain, "vk.com")
        return await get_vk_post(url)