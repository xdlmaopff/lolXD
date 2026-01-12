from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.database.queries import get_pending_verifications, update_verification_status, get_pending_orders, get_order, complete_order, get_user, get_verified_users, get_completed_orders, restore_order
from bot.keyboards.inline import get_admin_panel_keyboard, get_verifications_keyboard, get_order_actions_keyboard, get_completed_orders_keyboard
from bot.middlewares import AdminMiddleware
from bot.states import AdminStates
from bot.utils import notify_admin
from bot.config import YOUR_ADMIN_ID

router = Router()
router.message.middleware(AdminMiddleware([YOUR_ADMIN_ID]))
router.callback_query.middleware(AdminMiddleware([YOUR_ADMIN_ID]))

@router.message(F.text == "Админка")
async def admin_panel(message: Message) -> None:
    """Show admin panel."""
    keyboard = get_admin_panel_keyboard()
    await message.answer("Привет, админ!", reply_markup=keyboard)

@router.callback_query(F.data == "check_verifs")
async def check_verifications(callback: CallbackQuery, bot: Bot) -> None:
    """Show pending verifications."""
    verifs = get_pending_verifications()
    if not verifs:
        await callback.message.edit_text("Нет заявок на верификацию.")
        return

    await callback.message.edit_text("Заявки на верификацию:")
    for verif in verifs:
        user = get_user(verif.user_id)
        username = user.username if user and user.username else "без username"
        text = f"Username: @{username}\nID: {verif.user_id}\nИмя: {verif.name}\nВозраст: {verif.age}\nДеятельность: {verif.activity}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Принять", callback_data=f"approve_{verif.user_id}"),
             InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{verif.user_id}")]
        ])
        # Send document photo with buttons
        await bot.send_photo(callback.from_user.id, verif.document_photo,
                           caption=text, reply_markup=keyboard)



@router.callback_query(F.data == "active_orders")
async def show_active_orders(callback: CallbackQuery) -> None:
    """Show active orders."""
    orders = get_pending_orders()  # Actually, we need taken orders, not pending
    # TODO: Fix this - need query for taken orders
    if not orders:
        await callback.message.edit_text("Нет активных заказов.", reply_markup=get_admin_panel_keyboard())
        return

    text = "Активные заказы:\n\n"
    for order in orders:
        order_id, item, price, address, user_id = order
        order_obj = get_order(order_id)
        if order_obj and order_obj.drop_id:
            text += f"#{order_id} - {item} (${price:.2f})\nДроп: {order_obj.drop_id}\nКлиент: {user_id}\n\n"
            # Add complete button
            keyboard = get_order_actions_keyboard(order_id)
            await callback.message.answer(text, reply_markup=keyboard)
            text = ""  # Reset for next

    if not any(order_obj and order_obj.drop_id for order in [get_order(o[0]) for o in orders]):
        await callback.message.edit_text("Нет активных заказов.", reply_markup=get_admin_panel_keyboard())
    else:
        await callback.message.edit_text("Активные заказы показаны выше.", reply_markup=get_admin_panel_keyboard())

@router.callback_query(F.data.startswith("approve_"))
async def approve_verification(callback: CallbackQuery, bot: Bot) -> None:
    """Approve verification."""
    user_id = int(callback.data.split("_")[1])
    update_verification_status(user_id, 'verified')

    await bot.send_message(user_id, "Ваша заявка на верификацию принята. Теперь вы можете брать заказы.")
    await callback.answer("Принято", show_alert=True)
    await notify_admin(bot, f"Верификация пользователя {user_id} принята")

@router.callback_query(F.data.startswith("reject_"))
async def reject_verification(callback: CallbackQuery, bot: Bot) -> None:
    """Reject verification."""
    user_id = int(callback.data.split("_")[1])
    update_verification_status(user_id, 'rejected')

    await bot.send_message(user_id, "Ваша заявка на верификацию отклонена.")
    await callback.answer("Отклонено", show_alert=True)
    await notify_admin(bot, f"Верификация пользователя {user_id} отклонена")

@router.callback_query(F.data == "send_to_drops")
async def send_to_drops_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start sending message to all drops."""
    await state.set_state(AdminStates.send_to_drops)
    await callback.message.edit_text("Введите сообщение для отправки всем дропам:")
    await callback.answer()

@router.message(AdminStates.send_to_drops)
async def send_to_drops(message: Message, state: FSMContext, bot: Bot) -> None:
    """Send message to all verified drops."""
    text = message.text.strip()
    if not text:
        await message.answer("Сообщение не может быть пустым.")
        return

    drops = get_verified_users()
    sent_count = 0
    for drop in drops:
        try:
            await bot.send_message(drop.user_id, f"Сообщение от администратора:\n{text}")
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {drop.user_id}: {e}")

    await message.answer(f"Сообщение отправлено {sent_count} дропам.", reply_markup=get_admin_panel_keyboard())
    await state.clear()

@router.callback_query(F.data.startswith("complete_"))
async def complete_order_admin(callback: CallbackQuery, bot: Bot) -> None:
    """Complete order as admin."""
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    complete_order(order_id)

    await bot.send_message(order.user_id, f"Ваш заказ #{order_id} завершён.")
    if order.drop_id:
        await bot.send_message(order.drop_id, f"Заказ #{order_id} завершён.")

    await callback.answer("Заказ завершён", show_alert=True)
    await notify_admin(bot, f"Заказ #{order_id} завершён администратором")

@router.callback_query(F.data == "completed_orders")
async def show_completed_orders(callback: CallbackQuery) -> None:
    """Show completed orders for admin."""
    orders = get_completed_orders()
    if not orders:
        await callback.message.edit_text("Нет завершенных заказов.", reply_markup=get_admin_panel_keyboard())
        return

    text = "Завершенные заказы:\n\n"
    for order in orders:
        order_id, item, price, address, user_id = order
        order_obj = get_order(order_id)
        if order_obj:
            text += f"#{order_id} - {item} (${price:.2f})\nДроп: {order_obj.drop_id or 'нет'}\nКлиент: {user_id}\n\n"
            keyboard = get_completed_orders_keyboard(order_id)
            await callback.message.answer(text, reply_markup=keyboard)
            text = ""  # Reset

    await callback.message.edit_text("Завершенные заказы показаны выше.", reply_markup=get_admin_panel_keyboard())

@router.callback_query(F.data.startswith("restore_"))
async def restore_order_callback(callback: CallbackQuery, bot: Bot) -> None:
    """Restore order to pending."""
    order_id = int(callback.data.split("_")[1])
    restore_order(order_id)

    await callback.answer("Заказ восстановлен", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)
    await notify_admin(bot, f"Заказ #{order_id} восстановлен администратором")