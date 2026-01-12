from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_orders_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Keyboard for displaying orders to drops."""
    keyboard = []
    for order in orders:
        order_id, item, price, address, _ = order
        keyboard.append([
            InlineKeyboardButton(
                text=".2f",
                callback_data=f"take_{order_id}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="Пропустить",
                callback_data=f"skip_{order_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin panel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить верификации", callback_data="check_verifs")],
        [InlineKeyboardButton(text="Активные заказы", callback_data="active_orders")],
        [InlineKeyboardButton(text="Завершенные заказы", callback_data="completed_orders")],
        [InlineKeyboardButton(text="Отправить всем дропам", callback_data="send_to_drops")]
    ])

def get_verifications_keyboard(verifications: list) -> InlineKeyboardMarkup:
    """Keyboard for verification approvals."""
    keyboard = []
    for verif in verifications:
        keyboard.append([
            InlineKeyboardButton(
                text=f"@{verif.user_id} - Принять",
                callback_data=f"approve_{verif.user_id}"
            ),
            InlineKeyboardButton(
                text="Отклонить",
                callback_data=f"reject_{verif.user_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting activity type."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистрация банков", callback_data="activity_banks")],
        [InlineKeyboardButton(text="На карты", callback_data="activity_cards")],
        [InlineKeyboardButton(text="Верификация", callback_data="activity_verification")],
        [InlineKeyboardButton(text="Другое", callback_data="activity_other")]
    ])

def get_order_item_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting order item type."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистрация банков", callback_data="order_banks")],
        [InlineKeyboardButton(text="На карты", callback_data="order_cards")],
        [InlineKeyboardButton(text="Верификация", callback_data="order_verification")],
        [InlineKeyboardButton(text="Другое", callback_data="order_other")]
    ])

def get_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Admin keyboard for order actions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить", callback_data=f"complete_{order_id}")]
    ])

def get_completed_orders_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Admin keyboard for completed order actions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Восстановить", callback_data=f"restore_{order_id}")]
    ])

def get_active_orders_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Keyboard for drop's active orders."""
    keyboard = []
    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                text=f"Завершить заказ #{order.order_id}",
                callback_data=f"drop_complete_{order.order_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



from bot.database.models import User

def get_welcome_keyboard(user: User) -> InlineKeyboardMarkup:
    """Welcome keyboard with join drop and subscribe buttons."""
    keyboard = []
    if user.status not in ('verified', 'pending'):
        keyboard.append([InlineKeyboardButton(text="Стать дропом", callback_data="become_drop")])
    keyboard.append([InlineKeyboardButton(text="Подписаться на канал", url="https://t.me/+OCuwcSmh1hg0NTli")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)