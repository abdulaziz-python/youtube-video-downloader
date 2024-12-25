from django.contrib import admin
from .models import TelegramUser, VideoDownload, AdminMessage

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'joined_date')
    search_fields = ('user_id', 'username', 'first_name')
    readonly_fields = ('joined_date',)

@admin.register(VideoDownload)
class VideoDownloadAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'user', 'download_date')
    search_fields = ('video_id', 'user__username')
    readonly_fields = ('download_date',)

@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at')
    readonly_fields = ('created_at',)





# ==================+FOR BOT+=============================
