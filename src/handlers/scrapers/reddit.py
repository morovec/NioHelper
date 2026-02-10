import mimetypes
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.resources import path_to_media
from src.types.post import PostParsed

import httpx

# Константы
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@dataclass
class RedditMedia:
    path: Path
    content_type: str

@dataclass
class RedditPost:
    author: str
    title: str
    files: List[Path] = field(default_factory=list)

class RedditDownloader:
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _download_file(self, url: str, base_name: str="") -> Path:
        """Скачивает файл и возвращает объект Path с корректным расширением."""
        resp = await self.client.get(url)
        resp.raise_for_status()
        
        content_type = resp.headers.get("Content-Type", "image/png")
        ext = mimetypes.guess_extension(content_type) or ".png"
        
        file_path = Path(f"{path_to_media}{base_name}{ext}")
        file_path.write_bytes(resp.content)
        return file_path

    def _merge_video_audio(self, v_path: Path, a_path: Path, out_path: Path) -> Path:
        """Склеивает видео и аудио через FFmpeg."""
        cmd = [
            'ffmpeg', '-y', '-i', str(v_path), '-i', str(a_path),
            '-c', 'copy', str(out_path)
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return out_path
        finally:
            # Удаляем временные файлы в любом случае
            v_path.unlink(missing_ok=True)
            a_path.unlink(missing_ok=True)

    async def _get_audio_url_from_dash(self, base_url: str) -> Optional[str]:
        """Пытается найти URL аудио в DASH манифесте."""
        dash_url = f"{base_url}/DASHPlaylist.mpd"
        try:
            resp = await self.client.get(dash_url)
            if resp.status_code != 200:
                return None
            
            # Очистка XML от namespace для простоты
            xml_text = re.sub(r'\sxmlns="[^"]+"', '', resp.text, count=1)
            root = ET.fromstring(xml_text)
            
            # Ищем аудио потоки
            audio_elements = root.findall(".//AdaptationSet[@contentType='audio']/Representation/BaseURL")
            if audio_elements:
                return f"{base_url}/{audio_elements[-1].text}"
        except Exception as e:
            print(f"Ошибка парсинга DASH: {e}")
        return None

    async def _handle_video(self, data: dict, author: str) -> List[str]:
        video_info = data["secure_media"]["reddit_video"]
        video_url = video_info["fallback_url"]
        base_url = video_url.split('?')[0].rsplit('/', 1)[0]
        
        video_path = await self._download_file(video_url)
        audio_url = await self._get_audio_url_from_dash(base_url)
        
        if audio_url:
            audio_path = await self._download_file(audio_url, "audio")
            final_path = Path(f"{path_to_media}final.mp4")
            return [self._merge_video_audio(video_path, audio_path, final_path)]
        
        return [str(video_path)]

    async def _handle_gallery(self, data: dict, author: str) -> List[str]:
        files = []
        metadata = data.get("media_metadata", {})
        items = data.get("gallery_data", {}).get("items", [])
        
        for i, item in enumerate(items):
            m_id = item["media_id"]
            img_url = metadata[m_id]["s"]["u"].replace("&amp;", "&")
            path = await self._download_file(img_url, i)
            files.append(str(path))
        return files

    async def fetch_post(self, url: str) -> RedditPost:
        """Основной метод получения данных поста."""
        json_url = url.split('?')[0].rstrip('/') + ".json"
        resp = await self.client.get(json_url)
        resp.raise_for_status()
        
        post_data = resp.json()[0]["data"]["children"][0]["data"]
        author = post_data.get("author", "unknown")
        
        if post_data.get("is_video"):
            files = await self._handle_video(post_data, author)
        elif post_data.get("is_gallery"):
            files = await self._handle_gallery(post_data, author)
        else:
            media_url = post_data.get("url")
            files = [str(await self._download_file(media_url))]
            
        return PostParsed(author=author, media_paths=files)


reddit_downloader = RedditDownloader()
