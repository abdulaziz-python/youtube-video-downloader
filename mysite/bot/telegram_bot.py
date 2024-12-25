import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from aiogram.types import FSInputFile
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async
from .config import config
from .keyboards import Keyboards
from .models import TelegramUser, VideoDownload
import traceback
from .utils import (
    get_video_info, format_duration, format_number,
    log_user_action, get_bot_setting, is_user_admin_or_owner
)
from .admin_bot import admin_router
from .video_service import download_video_sync
from aiogram.utils.markdown import hbold
from aiogram.utils.text_decorations import markdown_decoration
from loguru import logger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot')

bot = Bot(token=config.TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router(name="main")


async def download_video(video_id: str):
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, download_video_sync, video_id)
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))





@router.message(Command("start"))
async def start_command(message: Message):
    user = message.from_user
    telegram_user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=str(user.id),
        defaults={
            'username': user.username,
            'first_name': user.first_name
        }
    )

    welcome_message = await get_bot_setting(
        'welcome_message',
        "🎉 *Welcome to YouTube Info Bot!*\n\n"
        "Send me a YouTube URL for video information!\n\n"
        "📌 Commands:\n"
        "/help - Show help\n"
        "/contact - Contact admin"
    )
    
    is_privileged = await is_user_admin_or_owner(str(user.id))
    keyboard = Keyboards.admin() if is_privileged else Keyboards.start()
    
    await message.answer(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await log_user_action(str(user.id), 'start_command')

@router.message(Command("admin"))
async def admin_command(message: Message):
    user_id = str(message.from_user.id)
    logger.info(f"Admin command accessed by user {user_id}")
    
    if not await is_user_admin_or_owner(user_id):
        logger.warning(f"Access denied for user {user_id}")
        await message.answer(
            "⛔️ Access denied. This command is only for administrators.",
            parse_mode="Markdown"
        )
        return

    await message.answer(
        "👨‍💼 *Admin Panel*\n\n"
        "Welcome to the administrative panel.\n"
        "Select an option below:",
        parse_mode="Markdown",
        reply_markup=Keyboards.admin()
    )
    await log_user_action(user_id, 'admin_panel_access')


@router.message(lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
async def process_youtube_url(message: Message):
    bot_username = (await bot.get_me()).username
    status = await message.answer("🎥 *Processing video\\.\\.\\.*", parse_mode="MarkdownV2")
    
    try:
        video_info = await get_video_info(message.text)
        
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(
            user_id=str(message.from_user.id),
            defaults={
                'username': message.from_user.username,
                'first_name': message.from_user.first_name
            }
        )
        
        await sync_to_async(VideoDownload.objects.create)(
            user=user,
            video_url=message.text,
            video_id=video_info['video_id']
        )

        duration_str = format_duration(video_info['duration'])

        caption = (
            f"🎥 *{escape_markdown_v2(video_info['title'])}*\n\n"
            f"👁️ Views: {escape_markdown_v2(format_number(video_info['views']))}\n"
            f"👍 Likes: {escape_markdown_v2(format_number(video_info['likes']))}\n"
            f"⏱️ Duration: {escape_markdown_v2(duration_str)}\n\n"
            f"🔍 Retrieved by: @{escape_markdown_v2(message.from_user.username or 'Anonymous')}\n"
            f"🤖 Via @{escape_markdown_v2(bot_username)}"
        )

        await message.answer_photo(
            photo=video_info['thumbnail'],
            caption=caption,
            parse_mode="MarkdownV2",
            reply_markup=Keyboards.video_info(video_info['video_id'])
        )

        await log_user_action(str(message.from_user.id), 'process_video', {'video_id': video_info['video_id']})
        await status.delete()

    except ValueError as e:
        error_message = (
            "❌ *Error processing video*\n\n"
            f"Error: {escape_markdown_v2(str(e))}\n\n"
            "Please make sure:\n"
            "• The URL is valid\n"
            "• The video is not private\n"
            "• The video exists"
        )
        await status.edit_text(error_message, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"Unexpected error in process_youtube_url: {e}")
        logger.error(traceback.format_exc())
        await status.edit_text(
            "❌ *An unexpected error occurred*\n\n"
            f"Error details: {escape_markdown_v2(str(e))}\n\n"
            "Please try again later or contact support\\.",
            parse_mode="MarkdownV2"
        )





@router.callback_query(lambda c: c.data.startswith("download_"))
async def handle_download(callback: CallbackQuery):
    try:
        video_id = callback.data.split("_")[1]
        loading_frames = ["⌛️", "⏳", "⌛️", "⏳"]
        status_message = await callback.message.answer(f"{loading_frames[0]} Initializing download...")
        frame_index = 0
        
        async def update_loading_animation():
            nonlocal frame_index
            while True:
                try:
                    frame_index = (frame_index + 1) % len(loading_frames)
                    await status_message.edit_text(
                        f"{loading_frames[frame_index]} Downloading video...\n"
                        "Please wait, this may take a few minutes."
                    )
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

        animation_task = asyncio.create_task(update_loading_animation())
        
        try:
            try:
                file_path, title, file_size = await download_video(video_id)
            except ValueError as e:
                if "exceeds the limit" in str(e):
                    size_mb = float(str(e).split('(')[1].split('MB')[0])
                    await status_message.edit_text(
                        f"⚠️ Video size ({size_mb:.1f}MB) exceeds Telegram's limit (20MB).\n\n"
                        "Options:\n"
                        "1. Try a shorter video\n"
                        "2. Contact admin for larger files\n"
                        "3. Use a different format/quality"
                    )
                    return
                else:
                    raise e
            
            animation_task.cancel()
            await status_message.edit_text("📤 Uploading to Telegram...")
            
            bot_info = await bot.get_me()
            
            video = FSInputFile(file_path)
            
            await callback.message.answer_video(
                video=video,
                caption=f"📥 *{title}*\n\nDownloaded via @{bot_info.username}",
                parse_mode="Markdown"
            )
            os.remove(file_path)
            await status_message.delete()
            
        except Exception as e:
            animation_task.cancel()
            logger.error(f"Download error: {e}")
            logger.error(traceback.format_exc())
            await status_message.edit_text(
                f"❌ Download failed: {str(e)}\n\n"
                "Please try again later or contact support."
            )
            
    except Exception as e:
        logger.error(f"Download handler error: {e}")
        logger.error(traceback.format_exc())
        await callback.answer(
            "❌ Download failed. Please try again or contact support.", 
            show_alert=True
        )





@router.callback_query(F.data == "help")
async def help_command(callback: CallbackQuery):
    help_text = (
        "🤖 *Bot Help*\n\n"
        "This bot helps you get information about YouTube videos.\n\n"
        "*How to use:*\n"
        "1. Send any YouTube video URL\n"
        "2. Get video information instantly\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/contact - Contact admin"
    )
    
    is_privileged = await is_user_admin_or_owner(str(callback.from_user.id))
    keyboard = Keyboards.admin() if is_privileged else Keyboards.start()
    
    await callback.message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "contact")
async def contact_command(callback: CallbackQuery):
    contact_text = (
        "📬 *Contact Information*\n\n"
        "To contact the admin, click the button below.\n"
        "Please be patient for the response!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Contact Admin",
                url=f"https://t.me/ablaze_coder"
            )],
            [InlineKeyboardButton(
                text="Back to Menu",
                callback_data="back_to_menu"
            )]
        ]
    )
    
    await callback.message.answer(
        contact_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "another_video")
async def another_video(callback: CallbackQuery):
    await callback.message.answer("Please send another YouTube URL.")
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    try:
        is_privileged = await is_user_admin_or_owner(str(callback.from_user.id))
        keyboard = Keyboards.admin() if is_privileged else Keyboards.start()
        
        current_text = callback.message.text
        new_text = "🎥 *YouTube Video Bot*\n\nSelect an option:"
        
        if current_text != new_text:
            await callback.message.edit_text(
                new_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.error(f"Error in back_to_menu: {e}")
    except Exception as e:
        logger.error(f"Error in back_to_menu: {e}")
    finally:
        await callback.answer()


        
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    try:
        is_privileged = await is_user_admin_or_owner(str(callback.from_user.id))
        keyboard = Keyboards.admin() if is_privileged else Keyboards.start()
        
        await callback.message.edit_text(
            "🎥 *YouTube Video Bot*\n\nSelect an option:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.error(f"Error in back_to_menu: {e}")
    except Exception as e:
        logger.error(f"Error in back_to_menu: {e}")
    finally:
        await callback.answer()


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(router)
    
    bot = Bot(token=config.TELEGRAM_TOKEN)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())



