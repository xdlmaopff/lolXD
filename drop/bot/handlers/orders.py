from aiogram import Router, F
from aiogram.types import Message
from bot.database.queries import get_user, get_user_orders, get_active_order_for_drop

router = Router()

@router.message(F.text == "Мои заказы")
async def show_user_orders(message: Message) -> None:
    """Show user's orders."""
    user_id = message.from_user.id
    orders = get_user_orders(user_id)

    if not orders:
        await message.answer("У вас нет заказов.")
        return

    text = "Ваши заказы:\n\n"
    for order in orders:
        status_text = {
            'pending': 'Ожидает',
            'taken': 'В работе',
            'completed': 'Завершён'
        }.get(order.status, order.status)
        text += f"#{order.order_id} - {order.item} (${order.price:.2f}) - {status_text}\n"

    await message.answer(text)

@router.message(F.text == "Активный заказ")
async def show_active_order(message: Message) -> None:
    """Show active order for drop."""
    user = get_user(message.from_user.id)
    if not user or user.status != 'verified':
        await message.answer("Только для верифицированных дропов.")
        return

    order = get_active_order_for_drop(user.user_id)
    if not order:
        await message.answer("У вас нет активного заказа.")
        return

    text = f"Активный заказ #{order.order_id}\n"
    text += f"Товар: {order.item}\n"
    text += f"Цена: ${order.price:.2f}\n"
    text += f"Адрес: {order.address}\n"
    text += f"Клиент: {order.user_id}"

    await message.answer(text)