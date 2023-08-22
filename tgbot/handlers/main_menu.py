from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery

from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc import reply_commands, messages
from tgbot.services.database.models import IikoUser
from tgbot.services.utils import update_user_from_api


async def send_profile(message: Message):
    db = message.bot.get('database')
    iiko = message.bot.get('iiko')
    async with db() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, message.from_id)
        iiko_user = await update_user_from_api(session, iiko, iiko_user.id)
        await message.answer(
            text=messages.profile.format(
                name=iiko_user.name or 'Не указано',
                birthday=iiko_user.birthday or 'Не указано',
                phone=iiko_user.phone,
                bonus_balance=iiko_user.bonus_balance
            ),
            reply_markup=inline_keyboards.profile
        )


async def show_profile(call: CallbackQuery):
    db = call.bot.get('database')
    iiko = call.bot.get('iiko')
    async with db() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, call.from_user.id)
        iiko_user = await update_user_from_api(session, iiko, iiko_user.id)
        await call.message.edit_text(
            text=messages.profile.format(
                name=iiko_user.name or 'Не указано',
                birthday=iiko_user.birthday or 'Не указано',
                phone=iiko_user.phone,
                bonus_balance=iiko_user.bonus_balance
            ),
            reply_markup=inline_keyboards.profile
        )
        await call.answer()


async def send_feedback_menu(message: Message):
    config = message.bot.get('config')
    await message.answer(messages.feedback_menu,
                         reply_markup=inline_keyboards.get_feedback_keyboard(config.misc.feedback_url))


async def send_reserve_table(message: Message):
    await message.answer('В разработке')


async def send_order_food(message: Message):
    await message.answer(messages.order_food, reply_markup=reply_keyboards.order)


def register_main_menu(dp: Dispatcher):
    dp.register_message_handler(send_profile, Text(equals=reply_commands.account))
    dp.register_callback_query_handler(show_profile, text='profile')
    dp.register_message_handler(send_feedback_menu, Text(equals=reply_commands.feedback))
    dp.register_message_handler(send_reserve_table, Text(equals=reply_commands.reserve_table))
    dp.register_message_handler(send_order_food, Text(equals=reply_commands.order_food))
