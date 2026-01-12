from aiogram.fsm.state import State, StatesGroup

class VerificationStates(StatesGroup):
    activity = State()
    name = State()
    age = State()
    document = State()

class OrderStates(StatesGroup):
    item = State()
    price = State()

class AdminStates(StatesGroup):
    send_to_drops = State()