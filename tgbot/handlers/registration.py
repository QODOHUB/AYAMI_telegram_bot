import datetime
import uuid

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType, ReplyKeyboardRemove

from tgbot.keyboards import reply_keyboards
from tgbot.misc import states, messages
from tgbot.services.database.models import IikoUser
from tgbot.services.iiko.schemas import ApiError, CreateOrUpdateCustomer
from tgbot.services.utils import contains_only_russian_letters


async def get_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number.replace('+', '')

    db = message.bot.get('database')
    async with db() as session:
        iiko = message.bot.get('iiko')
        try:
            customer = await iiko.get_customer_info('phone', phone)
        except ApiError:
            await message.answer(messages.name_input, reply_markup=ReplyKeyboardRemove())
            await states.Registration.next()
            await state.update_data(phone=phone)
        else:
            iiko_user = await IikoUser.create_or_update_from_api(session, customer)
            iiko_user.telegram_id = message.from_id
            await session.commit()
            await state.finish()
            await message.answer(messages.main_menu, reply_markup=reply_keyboards.main_menu)


async def get_name(message: Message, state: FSMContext):
    name = message.text
    if len(name) > 64:
        await message.answer(messages.name_too_long)
        return

    if not contains_only_russian_letters(name):
        await message.answer(messages.bad_name)
        return

    await message.answer(messages.birthday_input)
    await states.Registration.next()
    await state.update_data(name=name)


async def get_birthday(message: Message, state: FSMContext):
    birthday = message.text

    try:
        birthday = datetime.datetime.strptime(birthday, '%d.%m.%Y')
    except ValueError:
        await message.answer(messages.bad_birthday)
    else:
        state_data = await state.get_data()
        iiko = message.bot.get('iiko')
        new_customer = CreateOrUpdateCustomer(
            name=state_data['name'],
            phone=state_data['phone'],
            birthday=birthday
        )
        new_id = await iiko.create_or_update_customer(new_customer)

        new_iiko_user = IikoUser(
            id=new_id,
            name=state_data['name'],
            phone=state_data['phone'],
            birthday=birthday,
            telegram_id=message.from_id
        )
        db = message.bot.get('database')
        async with db() as session:
            session.add(new_iiko_user)
            await session.commit()
        await state.finish()
        await message.answer(messages.main_menu, reply_markup=reply_keyboards.main_menu)


def register_registration(dp: Dispatcher):
    dp.register_message_handler(get_contact, state=states.Registration.waiting_for_phone,
                                content_types=[ContentType.CONTACT])
    dp.register_message_handler(get_name, state=states.Registration.waiting_for_name)
    dp.register_message_handler(get_birthday, state=states.Registration.waiting_for_birthday)
