from django.db import models
from django.utils.crypto import get_random_string

class TelegramUser(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username or self.user_id}"

class VideoDownload(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    video_url = models.URLField()
    video_id = models.CharField(max_length=100)
    download_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.video_id} - {self.user}"

class AdminMessage(models.Model):
    text = models.TextField()
    photo_url = models.URLField(null=True, blank=True)
    inline_keyboard = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.created_at}"

class RequiredChannel(models.Model):
    channel_id = models.CharField(max_length=100, unique=True)
    channel_name = models.CharField(max_length=100)
    added_by = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True)
    added_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel_name} ({self.channel_id})"

class BotSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value):
        obj, created = cls.objects.update_or_create(key=key, defaults={'value': value})
        return obj

class UserAction(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    action_data = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action_type} at {self.timestamp}"

