from django.apps import AppConfig
from django.db.models.signals import post_migrate

class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    def ready(self):
        from .signals import create_default_settings
        post_migrate.connect(create_default_settings, sender=self)