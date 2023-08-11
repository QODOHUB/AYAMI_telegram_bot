from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.handlers.main_menu import send_profile
from tgbot.keyboards import reply_keyboards
from tgbot.misc import callbacks, states, messages
from tgbot.services.database.models import IikoUser
from tgbot.services.iiko.schemas import CreateOrUpdateCustomer
from tgbot.services.utils import contains_only_russian_letters


async def start_name_update(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(messages.new_name_input, reply_markup=reply_keyboards.cancel)
    await states.UpdateName.waiting_for_name.set()
    await call.answer()


async def get_new_name(message: Message, state: FSMContext):
    name = message.text
    if len(name) > 64:
        await message.answer(messages.name_too_long)
        return

    if not contains_only_russian_letters(name):
        await message.answer(messages.bad_name)
        return

    db = message.bot.get('database')
    async with db.begin() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, message.from_id)
        iiko_user.name = name

    iiko = message.bot.get('iiko')
    update_user = CreateOrUpdateCustomer(id=str(iiko_user.id), name=name)
    await iiko.create_or_update_customer(update_user)

    await state.finish()
    await message.answer(messages.name_updated.format(name=name), reply_markup=reply_keyboards.main_menu)
    await send_profile(message)


async def show_orders(call: CallbackQuery):
    await call.answer('В разработке', show_alert=True)


def register_profile(dp: Dispatcher):
    dp.register_callback_query_handler(start_name_update, callbacks.profile.filter(action='update_name'))
    dp.register_message_handler(get_new_name, state=states.UpdateName.waiting_for_name)

    dp.register_callback_query_handler(show_orders, callbacks.profile.filter(action='show_orders'))
