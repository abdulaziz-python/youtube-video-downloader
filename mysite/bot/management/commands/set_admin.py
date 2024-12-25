from django.core.management.base import BaseCommand
from django.db import transaction
from bot.models import TelegramUser

class Command(BaseCommand):
    help = 'Sets a user as admin or owner'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='Telegram user ID')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--admin', action='store_true', help='Set as admin')
        group.add_argument('--owner', action='store_true', help='Set as owner')
        group.add_argument('--remove', action='store_true', help='Remove admin/owner status')

    @transaction.atomic
    def handle(self, *args, **options):
        user_id = options['user_id']
        
        try:
            user = TelegramUser.objects.select_for_update().get(user_id=user_id)
            
            if options['admin']:
                user.is_admin = True
                user.is_owner = False
                status = 'admin'
            elif options['owner']:
                user.is_owner = True
                user.is_admin = True
                status = 'owner'
            elif options['remove']:
                user.is_admin = False
                user.is_owner = False
                status = 'regular user'
            
            user.save(update_fields=['is_admin', 'is_owner'])
            self.stdout.write(
                self.style.SUCCESS(f'User {user_id} set as {status}')
            )
            
        except TelegramUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {user_id} not found')
            )