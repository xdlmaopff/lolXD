from aiogram import Bot
from bot.config import ADMIN_CHAT_ID

async def notify_admin(bot: Bot, message: str) -> None:
    """Send notification to admin."""
    try:
        await bot.send_message(ADMIN_CHAT_ID, message)
    except Exception as e:
        print(f"Failed to notify admin: {e}")

def format_order_text(order) -> str:
    """Format order details for display."""
    if hasattr(order, 'order_id'):  # Order object
        return f"Заказ #{order.order_id}\nТовар: {order.item}\nБюджет: ${order.price:.2f}"
    else:  # tuple
        order_id, item, price, address, user_id = order
        return f"Заказ #{order_id}\nТовар: {item}\nБюджет: ${price:.2f}"