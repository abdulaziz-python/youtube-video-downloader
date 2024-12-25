import asyncio
from django.core.management.base import BaseCommand
from bot.telegram_bot import main as run_bot

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))
        try:
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Bot stopped'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running bot: {e}'))