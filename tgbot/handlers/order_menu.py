from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery

from tgbot.keyboards import reply_keyboards, inline_keyboards
from tgbot.misc import reply_commands, messages
from tgbot.services.database.models.group import Group
from tgbot.services.utils import update_menu_from_api


async def send_categories(message: Message):
    db = message.bot.get('database')
    iiko = message.bot.get('iiko')
    redis = message.bot.get('redis')

    async with db() as session:
        await update_menu_from_api(session, iiko, redis)
        main_groups = await Group.get_main_groups(session)

    await message.answer(messages.groups_choose, reply_markup=inline_keyboards.get_groups_keyboard(main_groups))


async def show_categories(call: CallbackQuery):
    db = call.bot.get('database')
    iiko = call.bot.get('iiko')
    redis = call.bot.get('redis')

    async with db() as session:
        await update_menu_from_api(session, iiko, redis)
        main_groups = await Group.get_main_groups(session)

    if call.message.photo:
        await call.message.delete()
        await call.message.answer(messages.groups_choose, reply_markup=inline_keyboards.get_groups_keyboard(main_groups))
    else:
        await call.message.edit_text(messages.groups_choose, reply_markup=inline_keyboards.get_groups_keyboard(main_groups))


async def send_cart(message: Message):
    await message.answer('В разработке')


async def send_main_menu(message: Message):
    await message.answer(messages.main_menu, reply_markup=reply_keyboards.main_menu)


def register_order_menu(dp: Dispatcher):
    dp.register_message_handler(send_categories, Text(equals=reply_commands.open_menu))
    dp.register_message_handler(send_cart, Text(equals=reply_commands.cart))
    dp.register_message_handler(send_main_menu, Text(equals=reply_commands.main_menu))
    dp.register_callback_query_handler(show_categories, text='groups')
