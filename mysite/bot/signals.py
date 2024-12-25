from django.db import transaction
from .models import BotSettings

DEFAULT_SETTINGS = {
    'welcome_message': (
        "🎉 *Welcome to YouTube Info Bot!*\n\n"
        "Send me a YouTube URL for video information!\n\n"
        "📌 Commands:\n"
        "/help - Show help\n"
        "/contact - Contact admin"
    ),
    'maintenance_mode': 'off',
    'max_daily_requests': '100',
}

def create_default_settings(sender, **kwargs):
    with transaction.atomic():
        for key, value in DEFAULT_SETTINGS.items():
            BotSettings.objects.get_or_create(
                key=key,
                defaults={'value': value}
            )