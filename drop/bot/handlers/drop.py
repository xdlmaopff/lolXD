from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database.queries import get_user, add_verification, get_pending_orders, get_order, take_order, get_active_orders_for_drop, get_active_order_for_drop, complete_order
from bot.keyboards.inline import get_orders_keyboard, get_activity_keyboard, get_active_orders_keyboard, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states import VerificationStates
from bot.utils import notify_admin, format_order_text
from bot.config import ADMIN_CHAT_ID

router = Router()

@router.message(F.text == "Стать дропом")
async def become_drop_start(message: Message, state: FSMContext) -> None:
    """Start drop verification process."""
    user_id = message.from_user.id
    username = message.from_user.username
    add_or_update_user(user_id, username)  # Ensure user is in db
    user = get_user(user_id)
    if user and user.status in ('verified', 'pending'):
        await message.answer("Ваша заявка уже подана или вы уже дроп.")
        return

    await state.set_state(VerificationStates.activity)
    keyboard = get_activity_keyboard()
    await message.answer("Выберите тип деятельности как дроп:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("activity_"), VerificationStates.activity)
async def process_activity_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Process activity selection."""
    activity_data = callback.data
    activity_map = {
        "activity_banks": "Регистрация банков",
        "activity_cards": "На карты",
        "activity_verification": "Верификация",
        "activity_other": "Другое"
    }
    activity = activity_map.get(activity_data, "Другое")

    await state.update_data(activity=activity)
    await state.set_state(VerificationStates.name)
    await callback.message.edit_text("Введите ваше имя:")
    await callback.answer()

@router.message(VerificationStates.activity)
async def process_activity(message: Message, state: FSMContext) -> None:
    """Process activity input if other."""
    activity = message.text.strip()
    if not activity:
        await message.answer("Расскажите о своей деятельности.")
        return

    await state.update_data(activity=activity)
    await state.set_state(VerificationStates.name)
    await message.answer("Введите ваше имя:")

@router.message(VerificationStates.name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Process name input."""
    name = message.text.strip()
    if not name:
        await message.answer("Имя не может быть пустым.")
        return

    await state.update_data(name=name)
    await state.set_state(VerificationStates.age)
    await message.answer("Введите ваш возраст (18+):")

@router.message(VerificationStates.age)
async def process_age(message: Message, state: FSMContext) -> None:
    """Process age input."""
    try:
        age = int(message.text.strip())
        if age < 14:
            await message.answer("Необходимо быть старше 14 лет.")
            return
    except ValueError:
        await message.answer("Введите корректный возраст.")
        return

    await state.update_data(age=age)
    await state.set_state(VerificationStates.document)
    await message.answer("Пришлите фото вашего паспорта или ID (опционально):")

@router.message(VerificationStates.document)
async def process_document(message: Message, state: FSMContext, bot: Bot) -> None:
    """Process document photo and submit verification."""
    photo_id = message.photo[-1].file_id if message.photo else "нет"
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or "без username"

    add_verification(user_id, data['name'], data['age'], photo_id, data['activity'])

    await message.answer("Заявка на верификацию отправлена. Ожидайте решения.")
    text = f"Новая заявка на верификацию:\n" \
           f"Username: @{username}\n" \
           f"ID: {user_id}\n" \
           f"Имя: {data['name']}\n" \
           f"Возраст: {data['age']}\n" \
           f"Деятельность: {data['activity']}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Принять", callback_data=f"approve_{user_id}"),
         InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}")]
    ])

    if photo_id != "нет":
        await bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=text, reply_markup=keyboard)
    else:
        await bot.send_message(ADMIN_CHAT_ID, text + "\nФото: нет", reply_markup=keyboard)

    await state.clear()

@router.message(F.text == "Заказы")
async def show_orders(message: Message, bot: Bot) -> None:
    """Show available orders to verified drops."""
    user = get_user(message.from_user.id)
    if not user or user.status != 'verified':
        await message.answer("Только для верифицированных дропов.")
        return

    # Check if drop already has an active order
    active_orders = get_active_orders_for_drop(user.user_id)
    if active_orders:
        await message.answer("У вас уже есть активный заказ. Завершите его перед взятием нового.")
        return

    orders = get_pending_orders()
    if not orders:
        await message.answer("Нет доступных заказов.")
        return

    text = "Доступные заказы:\n\n"
    keyboard = get_orders_keyboard(orders)

    for order in orders:
        text += format_order_text(order) + "\n\n"

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("take_"))
async def take_order_callback(callback: CallbackQuery, bot: Bot) -> None:
    """Handle order taking."""
    order_id = int(callback.data.split("_")[1])
    drop_id = callback.from_user.id

    user = get_user(drop_id)
    if not user or user.status != 'verified':
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    # Check if drop already has an active order
    active_orders = get_active_orders_for_drop(drop_id)
    if active_orders:
        await callback.answer("У вас уже есть активный заказ.", show_alert=True)
        return

    order = get_order(order_id)
    if not order or order.status != 'pending':
        await callback.answer("Заказ уже взят или недоступен.", show_alert=True)
        return

    take_order(order_id, drop_id)

    await callback.answer("Заказ взят!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)

    # Notify drop and client
    await bot.send_message(drop_id, f"Вы взяли заказ #{order_id}. Администратор свяжет вас с клиентом.")
    await bot.send_message(order.user_id, f"Ваш заказ #{order_id} взят в работу. Администратор свяжет вас с дропом.")

    await notify_admin(bot, f"Заказ #{order_id} взят дропом {drop_id}")

@router.callback_query(F.data.startswith("skip_"))
async def skip_order_callback(callback: CallbackQuery) -> None:
    """Handle order skipping."""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Заказ пропущен.", show_alert=True)

@router.message(F.text == "Активные заказы")
async def show_active_orders(message: Message) -> None:
    """Show active orders for drop."""
    user = get_user(message.from_user.id)
    if not user or user.status != 'verified':
        await message.answer("Только для верифицированных дропов.")
        return

    orders = get_active_orders_for_drop(user.user_id)
    if not orders:
        await message.answer("У вас нет активных заказов.")
        return

    text = "Ваши активные заказы:\n\n"
    for order in orders:
        text += format_order_text(order) + "\n\n"

    keyboard = get_active_orders_keyboard(orders)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("drop_complete_"))
async def drop_complete_order_callback(callback: CallbackQuery, bot: Bot) -> None:
    """Handle order completion by drop."""
    order_id = int(callback.data.split("_")[2])
    drop_id = callback.from_user.id

    user = get_user(drop_id)
    if not user or user.status != 'verified':
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    order = get_order(order_id)
    if not order or order.drop_id != drop_id or order.status != 'taken':
        await callback.answer("Заказ не найден или недоступен.", show_alert=True)
        return

    complete_order(order_id)

    await callback.answer("Заказ завершён!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)

    # Notify client and admin
    await bot.send_message(order.user_id, f"Ваш заказ #{order_id} завершён.")
    await bot.send_message(drop_id, f"Заказ #{order_id} завершён.")
    await notify_admin(bot, f"Дроп {drop_id} завершил заказ #{order_id}")