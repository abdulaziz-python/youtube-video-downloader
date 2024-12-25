import logging
from typing import Dict, Any
from googleapiclient.discovery import build
from urllib.parse import parse_qs, urlparse
import isodate
from asgiref.sync import sync_to_async
from .models import BotSettings, UserAction, TelegramUser
from django.db.models import Q
from .config import config
import asyncio
from typing import Tuple, Optional

logger = logging.getLogger('bot')


def get_video_info_sync(video_id: str) -> Dict[str, Any]:
    youtube = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
    
    video_response = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    ).execute()

    if not video_response.get('items'):
        raise ValueError("Video not found")

    video = video_response['items'][0]
    duration = isodate.parse_duration(video['contentDetails']['duration'])
    duration_seconds = int(duration.total_seconds())

    return {
        'video_id': video_id,
        'title': video['snippet']['title'],
        'thumbnail': video['snippet']['thumbnails']['high']['url'],
        'duration': duration_seconds,
        'views': int(video['statistics'].get('viewCount', 0)),
        'likes': int(video['statistics'].get('likeCount', 0))
    }


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
    return f"{int(minutes):02d}:{int(seconds):02d}"

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def get_video_size(url: str) -> Optional[int]:
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('filesize') or info.get('filesize_approx')
    except Exception as e:
        logger.error(f"Error getting video size: {e}")
        return None

def download_video_sync(video_id: str, use_local_api: bool = False) -> Tuple[str, str, int]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    file_size = get_video_size(url)
    if file_size:
        size_limit = config.LOCAL_API_LIMIT if use_local_api else config.TELEGRAM_BOT_API_LIMIT
        if file_size > size_limit:
            raise ValueError(
                f"Video size ({file_size / (1024*1024):.1f}MB) exceeds the limit "
                f"({size_limit / (1024*1024):.1f}MB). "
                f"{'Please contact admin for larger files.' if not use_local_api else 'File is too large to process.'}"
            )
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', 'N/A')
                total = d.get('_total_bytes_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                logger.info(f"Downloading: {percent} of {total} at {speed} ETA: {eta}")
            except Exception as e:
                logger.error(f"Progress hook error: {e}")
    
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'downloads/{video_id}.%(ext)s',
        'max_filesize': size_limit,
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
            actual_size = os.path.getsize(file_path)
        
        return file_path, title, actual_size
    except Exception as e:
        logger.error(f"Download error for video {video_id}: {e}")
        raise ValueError(f"Failed to download video: {str(e)}")





async def get_video_info(video_url: str) -> Dict[str, Any]:
    try:
        clean_url = clean_youtube_url(video_url)
        video_id = clean_url.split('v=')[1]

        loop = asyncio.get_running_loop()
        video_info = await loop.run_in_executor(None, get_video_info_sync, video_id)
        return video_info

    except Exception as e:
        logger.error(f"Error in get_video_info: {e}")
        raise ValueError(str(e))


async def log_user_action(user_id: str, action_type: str, action_data: dict = None):
    try:
        @sync_to_async
        def _log_action():
            user = TelegramUser.objects.get(user_id=user_id)
            UserAction.objects.create(
                user=user,
                action_type=action_type,
                action_data=action_data or {}
            )
        await _log_action()
        logger.info(f"User {user_id} performed action: {action_type}")
    except Exception as e:
        logger.error(f"Error logging user action: {e}")



async def get_bot_setting(key: str, default: Any = None) -> Any:
    @sync_to_async
    def _get_setting():
        return BotSettings.get(key, default)
    
    return await _get_setting()



async def set_bot_setting(key: str, value: Any):
    @sync_to_async
    def _set_setting():
        BotSettings.set(key, value)
        logger.info(f"Bot setting updated: {key}")

    await _set_setting()



async def is_user_admin(user_id: str) -> bool:
    @sync_to_async
    def _check_admin():
        return TelegramUser.objects.filter(
            user_id=user_id, 
            is_admin=True
        ).exists()
    
    return await _check_admin()



async def is_user_owner(user_id: str) -> bool:
    @sync_to_async
    def _check_owner():
        return TelegramUser.objects.filter(
            user_id=user_id, 
            is_owner=True
        ).exists()
    
    return await _check_owner()



def clean_youtube_url(url: str) -> str:
    try:
        if 'youtube.com' in url:
            query = parse_qs(urlparse(url).query)
            video_id = query.get('v', [None])[0]
        elif 'youtu.be' in url:
            video_id = url.split('/')[-1].split('?')[0]
        else:
            raise ValueError("Invalid YouTube URL")

        if not video_id:
            raise ValueError("Could not extract video ID")

        return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        logger.error(f"Error cleaning YouTube URL: {e}")
        raise ValueError("Invalid YouTube URL format")


async def is_user_admin_or_owner(user_id: str) -> bool:
    @sync_to_async
    def _check_status():
        return TelegramUser.objects.filter(
            user_id=user_id
        ).filter(
            Q(is_admin=True) | Q(is_owner=True)
        ).exists()
    
    return await _check_status()


