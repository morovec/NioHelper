from config import vk_user as vk
from src.vk.media import media_downloader
from src.handlers import file_save_from_url
from src.types.post import PostParsed
from src.resources.datas import path_to_media

from vkbottle_types.objects import WallWallpostAttachmentType

async def get_vk_post(url: str):
    post = url.split("wall")[-1]
    data = (await vk.api.wall.get_by_id(posts=post)).items[0]

    owner_id = data.owner_id
    attachments = data.attachments

    if owner_id < 0:
        # Для групп
        group_info = await vk.api.groups.get_by_id(group_id=abs(owner_id))
        name = group_info.groups[0].name
        author = f"[club{abs(owner_id)}|{name}]"
    else:
        # Для пользователей
        user_info = await vk.api.users.get(user_ids=owner_id)
        name = f"{user_info[0].first_name} {user_info[0].last_name}"
        author = f"[id{owner_id}|{name}]"




    c = 0
    paths = []
    for attachment in attachments:
        c += 1
        if attachment.type == WallWallpostAttachmentType.VIDEO:
            video_data = media_downloader.video(attachment.video)
            path = f"{path_to_media}{c}.mp4"
            file_save_from_url(path=path,
                               url=video_data["url"],
                               headers=video_data["headers"])
            paths.append(path)
        
        elif attachment.type == WallWallpostAttachmentType.PHOTO:
            path = f"{path_to_media}{c}.png"
            maxx = 0
            for size in attachment.photo.sizes:
                if size.height > maxx:
                    maxx = size.height
                    media_url = size.url
            
            file_save_from_url(path=path,
                               url=media_url)
            paths.append(path)
    
    vk_data = PostParsed(media_paths=paths,
                         author=author)
    return vk_data

        