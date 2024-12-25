from django.core.management.base import BaseCommand
from bot.models import TelegramUser

class Command(BaseCommand):
    help = 'Sets or verifies owner status for a Telegram user'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='Telegram user ID')

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        try:
            user = TelegramUser.objects.get(user_id=user_id)
            user.is_owner = True
            user.is_admin = True  
            user.save(update_fields=['is_owner', 'is_admin'])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully set user {user_id} as owner and admin'
                )
            )
            
        except TelegramUser.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f'User {user_id} not found. Start the bot first with this account.'
                )
            )   