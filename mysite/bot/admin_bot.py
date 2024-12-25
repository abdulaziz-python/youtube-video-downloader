from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from .models import TelegramUser, VideoDownload, BotSettings
from .keyboards import Keyboards
from .utils import format_number, is_user_admin, is_user_owner, is_user_admin_or_owner
import logging

logger = logging.getLogger('bot')

class AdminStates(StatesGroup):
    awaiting_broadcast = State()
    awaiting_admin_id = State()
    awaiting_welcome_message = State()

admin_router = Router(name="admin")

@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    user_id = str(message.from_user.id)
    if not await is_user_admin_or_owner(user_id):
        await message.answer("Access denied")
        return
        
    await message.answer(
        "👨‍💼 *Admin Panel*\n\nSelect an option:",
        parse_mode="Markdown",
        reply_markup=Keyboards.admin()
    )

@admin_router.callback_query(F.data == "broadcast")
async def handle_broadcast(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    if not await is_user_admin_or_owner(user_id):
        await callback.answer("Access denied", show_alert=True)
        return

    await callback.message.edit_text(
        "📣 Send your broadcast message\n\nFormat:\n- Simple text\n- photo_url|caption\n- text|button_text|button_url",
        reply_markup=Keyboards.back_admin()
    )
    await state.set_state(AdminStates.awaiting_broadcast)
    await callback.answer()

@admin_router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    if not await is_user_admin_or_owner(user_id):
        await callback.answer("Access denied", show_alert=True)
        return

    total_users = await sync_to_async(TelegramUser.objects.count)()
    total_downloads = await sync_to_async(VideoDownload.objects.count)()
    
    stats_text = (
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: {format_number(total_users)}\n"
        f"📥 Total Downloads: {format_number(total_downloads)}"
    )
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=Keyboards.admin()
    )
    await callback.answer()

@admin_router.callback_query(F.data == "manage_admins")
async def manage_admins(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    if not await is_user_owner(user_id):
        await callback.answer("Only owner can access this", show_alert=True)
        return

    admins = await sync_to_async(list)(TelegramUser.objects.filter(is_admin=True))
    admin_list = "\n".join(f"@{admin.username or admin.user_id}" for admin in admins)
    
    await callback.message.edit_text(
        f"Current admins:\n{admin_list}\n\nTo add admin, send their Telegram ID:",
        reply_markup=Keyboards.back_admin()
    )
    await state.set_state(AdminStates.awaiting_admin_id)
    await callback.answer()

@admin_router.callback_query(F.data == "bot_settings")
async def show_bot_settings(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    if not await is_user_admin_or_owner(user_id):
        await callback.answer("Access denied", show_alert=True)
        return

    await callback.message.edit_text(
        "⚙️ *Bot Settings*\n\nSelect option:",
        parse_mode="Markdown",
        reply_markup=Keyboards.bot_settings()
    )
    await callback.answer()

@admin_router.callback_query(F.data == "change_welcome")
async def change_welcome_message(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    if not await is_user_admin_or_owner(user_id):
        await callback.answer("Access denied", show_alert=True)
        return

    await callback.message.edit_text(
        "Send the new welcome message:",
        reply_markup=Keyboards.back_admin()
    )
    await state.set_state(AdminStates.awaiting_welcome_message)
    await callback.answer()

@admin_router.message(AdminStates.awaiting_welcome_message)
async def process_welcome_message(message: Message, state: FSMContext):
    if not await is_user_admin_or_owner(str(message.from_user.id)):
        return

    await sync_to_async(BotSettings.set)('welcome_message', message.text)
    await message.answer(
        "✅ Welcome message updated!",
        reply_markup=Keyboards.admin()
    )
    await state.clear()

@admin_router.message(AdminStates.awaiting_admin_id)
async def process_new_admin(message: Message, state: FSMContext):
    if not await is_user_owner(str(message.from_user.id)):
        return

    try:
        user_id = message.text.strip()
        user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
        user.is_admin = True
        await sync_to_async(user.save)()
        
        await message.answer(
            f"✅ User {user_id} is now admin!",
            reply_markup=Keyboards.admin()
        )
    except TelegramUser.DoesNotExist:
        await message.answer(
            f"❌ User {user_id} not found",
            reply_markup=Keyboards.admin()
        )
    
    await state.clear()

@admin_router.message(AdminStates.awaiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not await is_user_admin_or_owner(str(message.from_user.id)):
        return

    try:
        parts = message.text.split('|')
        users = await sync_to_async(list)(TelegramUser.objects.all())
        
        for user in users:
            try:
                if len(parts) == 1:
                    await message.bot.send_message(
                        user.user_id,
                        text=parts[0],
                        parse_mode="Markdown"
                    )
                elif len(parts) == 2:
                    await message.bot.send_photo(
                        user.user_id,
                        photo=parts[0],
                        caption=parts[1],
                        parse_mode="Markdown"
                    )
                elif len(parts) == 3:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text=parts[1], url=parts[2])
                    ]])
                    await message.bot.send_message(
                        user.user_id,
                        text=parts[0],
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Broadcast error for user {user.user_id}: {e}")
                continue

        await message.reply(
            "✅ Broadcast sent!",
            reply_markup=Keyboards.admin()
        )
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await message.reply(
            "❌ Broadcast failed",
            reply_markup=Keyboards.admin()
        )
    finally:
        await state.clear()