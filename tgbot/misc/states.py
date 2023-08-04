from aiogram.dispatcher.filters.state import StatesGroup, State


class Registration(StatesGroup):
    waiting_for_phone = State()  # Add 'phone' to data if iiko user doesn't exist
    waiting_for_name = State()  # Add 'name' to data
    waiting_for_birthday = State()


class UpdateName(StatesGroup):
    waiting_for_name = State()
