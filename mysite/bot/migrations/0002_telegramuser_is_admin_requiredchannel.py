# Generated by Django 5.0.9 on 2024-12-21 11:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramuser',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='RequiredChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=100, unique=True)),
                ('channel_name', models.CharField(max_length=100)),
                ('added_date', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.telegramuser')),
            ],
        ),
    ]