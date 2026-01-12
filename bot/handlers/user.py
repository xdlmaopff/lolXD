import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.database.queries import add_or_update_user, get_user, add_order
from bot.keyboards.reply import get_main_keyboard
from bot.keyboards.inline import get_order_item_keyboard, get_welcome_keyboard
from bot.states import OrderStates
from bot.utils import notify_admin
from bot.config import YOUR_ADMIN_ID

router = Router()

@router.message(F.text == "/start")
async def start_handler(message: Message, bot: Bot) -> None:
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username

    add_or_update_user(user_id, username)
    user = get_user(user_id)

    welcome_keyboard = get_welcome_keyboard(user)
    reply_keyboard = get_main_keyboard(user)
    await message.answer_photo(
        photo=FSInputFile(os.path.join(os.path.dirname(os.path.dirname(__file__)), "ДропХата.png")),
        caption="Добро пожаловать в ДропХату!\n\n"
        "Здесь вы можете найти надёжных дропов для выполнения заказов или стать дропом и зарабатывать.\n\n"
        "Выберите действие ниже:",
        reply_markup=welcome_keyboard
    )
    await message.answer("Меню:", reply_markup=reply_keyboard)

@router.message(F.text == "Профиль")
async def profile_handler(message: Message) -> None:
    """Show user profile."""
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        await message.answer("Пользователь не найден.")
        return

    username = user.username or "без username"
    name = user.name or f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or "не указано"
    if not user.name:
        # Try to get name from verifications
        from bot.database.queries import get_user_verification
        verif = get_user_verification(user_id)
        if verif and verif.name:
            name = verif.name
    if user.status == 'verified':
        role = "Дроп"
    elif user.status == 'pending':
        role = "Ожидает верификации"
    elif user.status == 'rejected':
        role = "Верификация отклонена"
    else:
        role = "Клиент"

    if user_id == YOUR_ADMIN_ID:
        text = f"Профиль:\n" \
               f"ID: {user_id}\n" \
               f"Тег: @{username}\n" \
               f"Имя: {name}\n" \
               f"Должность: Администратор"
    else:
        text = f"Профиль:\n" \
               f"Имя: {name}\n" \
               f"Должность: {role}"

    await message.answer_photo(
        photo=FSInputFile(os.path.join(os.path.dirname(os.path.dirname(__file__)), "ДропХата.png")),
        caption=text
    )

@router.callback_query(F.data == "become_drop")
async def become_drop_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle become drop from inline button."""
    from bot.keyboards.inline import get_activity_keyboard
    from bot.states import VerificationStates

    user = get_user(callback.from_user.id)
    if user and user.status in ('verified', 'pending'):
        await callback.message.answer("Ваша заявка уже подана или вы уже дроп.")
        await callback.answer()
        return

    await state.set_state(VerificationStates.activity)
    keyboard = get_activity_keyboard()
    await callback.message.answer("Выберите тип деятельности как дроп:", reply_markup=keyboard)
    await callback.answer()

@router.message(F.text == "Сделать заказ")
async def create_order_start(message: Message, state: FSMContext) -> None:
    """Start order creation process."""
    await state.set_state(OrderStates.item)
    keyboard = get_order_item_keyboard()
    await message.answer("Выберите тип заказа:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("order_"), OrderStates.item)
async def process_order_item_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Process order item selection."""
    item_data = callback.data
    if item_data == "order_other":
        await callback.message.edit_text("Введите описание заказа:")
        await callback.answer()
        return

    item_map = {
        "order_banks": "Регистрация банков",
        "order_cards": "На карты",
        "order_verification": "Верификация"
    }
    item = item_map.get(item_data, "Другое")

    await state.update_data(item=item)
    await state.set_state(OrderStates.price)
    await callback.message.edit_text("Сколько вы готовы заплатить за заказ (в USD, например, 50.00):")
    await callback.answer()

@router.message(OrderStates.item)
async def process_item(message: Message, state: FSMContext) -> None:
    """Process custom item input for 'other'."""
    item = message.text.strip()
    if not item:
        await message.answer("Описание заказа не может быть пустым.")
        return

    await state.update_data(item=item)
    await state.set_state(OrderStates.price)
    await message.answer("Сколько вы готовы заплатить за заказ (в USD, например, 50.00):")

@router.message(OrderStates.price)
async def process_price(message: Message, state: FSMContext, bot: Bot) -> None:
    """Process price input and create order."""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную цену.")
        return

    await state.update_data(price=price)
    data = await state.get_data()
    user_id = message.from_user.id

    order_id = add_order(user_id, data['item'], data['price'], "")

    await message.answer(f"Заказ #{order_id} принят. Администратор свяжет вас с дропом.")
    await notify_admin(bot, f"Новый заказ #{order_id} от пользователя {user_id}")
    await state.clear()



