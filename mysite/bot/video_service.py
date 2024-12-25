import os
import logging
from typing import Tuple, Optional
import yt_dlp
from pathlib import Path

logger = logging.getLogger(__name__)

def get_video_size(url: str) -> Optional[int]:
    """Get video file size before downloading."""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            best_format = next((f for f in formats if f.get('format_id') == info.get('format_id')), None)
            return best_format.get('filesize') if best_format else None
    except Exception as e:
        logger.error(f"Error getting video size: {str(e)}")
        return None

def ensure_download_directory():
    """Ensure downloads directory exists."""
    Path('downloads').mkdir(exist_ok=True)

def download_video_sync(video_id: str) -> Tuple[str, str, int]:
    """
    Download YouTube video synchronously.
    Returns: (file_path, title, file_size)
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ensure_download_directory()
    
    file_size = get_video_size(url)
    if file_size and file_size > (20 * 1024 * 1024): 
        raise ValueError(f"Video size ({file_size / (1024*1024):.1f}MB) exceeds Telegram's limit (20MB)")

    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0)
                if total > 0:
                    progress = (downloaded / total) * 100
                    logger.info(f"Download progress: {progress:.1f}%")
            except Exception as e:
                logger.error(f"Progress hook error: {str(e)}")

    ydl_opts = {
        'format': 'best[filesize<20M][ext=mp4]/best[filesize<20M]',  
        'outtmpl': f'downloads/{video_id}.%(ext)s',
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Could not fetch video information")
            
            formats = info.get('formats', [])
            suitable_format = None
            for fmt in formats:
                size = fmt.get('filesize')
                if size and size <= (20 * 1024 * 1024):
                    suitable_format = fmt
                    break
            
            if not suitable_format:
                raise ValueError("No suitable format found under 20MB")
            
            ydl_opts['format'] = suitable_format['format_id']
            info = ydl.extract_info(url, download=True)
            
            file_path = ydl.prepare_filename(info)
            if not os.path.exists(file_path):
                base_path = os.path.splitext(file_path)[0]
                for ext in ['mp4', 'mkv', 'webm']:
                    alt_path = f"{base_path}.{ext}"
                    if os.path.exists(alt_path):
                        file_path = alt_path
                        break
            
            if not os.path.exists(file_path):
                raise ValueError("Downloaded file not found")
            
            actual_size = os.path.getsize(file_path)
            if actual_size > (20 * 1024 * 1024):
                os.remove(file_path)
                raise ValueError("Downloaded file exceeds size limit")
            
            return file_path, info.get('title', 'Video'), actual_size
            
    except Exception as e:
        logger.error(f"Download error for video {video_id}: {str(e)}")

        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise ValueError(f"Failed to download video: {str(e)}")