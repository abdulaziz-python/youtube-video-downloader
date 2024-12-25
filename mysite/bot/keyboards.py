from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Keyboards:
    @staticmethod
    def start() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Get Video Info", callback_data="download")],
            [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
            [InlineKeyboardButton(text="📞 Contact Admin", callback_data="contact")]
        ])

    @staticmethod
    def admin() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="broadcast")],
            [InlineKeyboardButton(text="📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton(text="👥 Manage Admins", callback_data="manage_admins")],
            [InlineKeyboardButton(text="⚙️ Bot Settings", callback_data="bot_settings")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
        ])

    @staticmethod
    def back_admin() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Admin", callback_data="admin")]
        ])

    @staticmethod
    def bot_settings() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Welcome Message", callback_data="change_welcome")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="admin")]
        ])

    @staticmethod
    def video_info(video_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Download Video", callback_data=f"download_{video_id}"), 
                InlineKeyboardButton(text="🔄 Another Video", callback_data="another_video")],
            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_menu")]
        ])

    @staticmethod
    def confirm_action() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes", callback_data="confirm"),
                InlineKeyboardButton(text="❌ No", callback_data="cancel")
            ]
        ])