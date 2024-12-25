from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
    YOUTUBE_API_KEY: str = os.getenv('YOUTUBE_API_KEY')
    YOUTUBE_API_SCOPES: List[str] = (
        'https://www.googleapis.com/auth/youtube.readonly',
    )
    TELEGRAM_BOT_API_LIMIT: int = 20 * 1024 * 1024
    LOCAL_API_LIMIT: int = 2 * 1024 * 1024 * 1024
    SUPPORTED_FORMATS: List[str] = ('mp4', 'webm')
    DOWNLOAD_TIMEOUT: int = 300
    MAX_DOWNLOAD_ATTEMPTS: int = 1000
    OWNER_USERNAME: str = os.getenv('OWNER_USERNAME', '')
    MAX_CAPTION_LENGTH: int = 1024
    TELEGRAM_BOT_API_LIMIT = 20 * 1024 * 1024


    @property
    def logging_config(self) -> dict:
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {message}',
                    'style': '{',
                },
            },
            'handlers': {
                'file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': 'bot.log',
                    'formatter': 'verbose',
                },
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'bot': {
                    'handlers': ['file', 'console'],
                    'level': 'INFO',
                    'propagate': True,
                },
            },
        }

config = Config()