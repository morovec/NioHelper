import requests
from src.handlers import file_save_from_url
from src.resources.datas import path_to_media

from src.types.post import PostParsed

def get_tweet(url: str) -> dict:
    r = requests.get(url)

    result = r.json()

    author = result["tweet"]["author"]["screen_name"]
    media = result["tweet"]["media"]
    i = 0
    media_paths = []
    if "photos" in media:
        for photo in media["photos"]:
            i += 1
            path = f"{path_to_media}{i}.png"
            file_save_from_url(path, photo["url"], True)
            media_paths.append(path)
    if "videos" in media:
        for video in media["videos"]:
            i += 1
            path = f"{path_to_media}{i}.mp4"
            file_save_from_url(path, video["url"], True)
            media_paths.append(path)

    x_data = PostParsed(media_paths=media_paths,
                             author=author)
    
    return x_data