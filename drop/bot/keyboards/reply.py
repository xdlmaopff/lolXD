from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.database.models import User
from bot.config import YOUR_ADMIN_ID

def get_main_keyboard(user: User) -> ReplyKeyboardMarkup:
    """Generate main keyboard based on user status."""
    keyboard = [
        [KeyboardButton(text="Профиль"), KeyboardButton(text="Сделать заказ")]
    ]

    if user.status == 'verified':
        keyboard.append([KeyboardButton(text="Заказы")])

    if user.user_id == YOUR_ADMIN_ID:
        keyboard.append([KeyboardButton(text="Админка")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите действие"
    )