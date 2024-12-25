import os
import asyncio
import aiohttp
from typing import Tuple
import logging
from googleapiclient.discovery import build
from .config import config

logger = logging.getLogger('bot')

async def download_video(video_id: str) -> Tuple[str, str]:
    try:
        youtube = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
        video_response = youtube.videos().list(
            part="snippet,contentDetails",
            id=video_id
        ).execute()

        if not video_response.get('items'):
            raise ValueError("Video not found")

        video = video_response['items'][0]
        title = video['snippet']['title']

        video_url = f"https://www.youtube.com/get_video_info?video_id={video_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    raise ValueError("Failed to get video info")
                
                os.makedirs('downloads', exist_ok=True)
                file_path = os.path.join('downloads', f"{video_id}.mp4")
                
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                return file_path, title

    except Exception as e:
        logger.error(f"Download error for video {video_id}: {e}")
        raise ValueError(f"Failed to download video: {str(e)}")