from aiogram.dispatcher.filters.state import StatesGroup, State


class Registration(StatesGroup):
    waiting_for_phone = State()  # Add 'phone' to data if iiko user doesn't exist
    waiting_for_name = State()  # Add 'name' to data
    waiting_for_birthday = State()


class UpdateName(StatesGroup):
    waiting_for_name = State()


class Order(StatesGroup):
    waiting_for_city = State()
    waiting_for_street = State()
    waiting_for_house = State()
    waiting_for_entrance = State()
    waiting_for_floor = State()
    waiting_for_flat = State()
    waiting_for_comment = State()

    finishing = State()
