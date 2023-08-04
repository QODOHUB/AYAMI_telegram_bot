from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

from tgbot.keyboards import inline_keyboards
from tgbot.misc import reply_commands, messages
from tgbot.services.database.models import IikoUser


async def send_profile(message: Message):
    db = message.bot.get('database')
    async with db() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, message.from_id)
        await message.answer(
            text=messages.profile.format(
                name=iiko_user.name or 'Не указано',
                birthday=iiko_user.birthday or 'Не указано',
                phone=iiko_user.phone,
                bonus_balance=iiko_user.bonus_balance
            ),
            reply_markup=inline_keyboards.profile
        )


async def send_feedback_menu(message: Message):
    config = message.bot.get('config')
    await message.answer(messages.feedback_menu,
                         reply_markup=inline_keyboards.get_feedback_keyboard(config.misc.feedback_url))


async def send_reserve_table(message: Message):
    await message.answer('В разработке')


async def send_order_food(message: Message):
    await message.answer('В разработке')


def register_main_menu(dp: Dispatcher):
    dp.register_message_handler(send_profile, Text(equals=reply_commands.account))
    dp.register_message_handler(send_feedback_menu, Text(equals=reply_commands.feedback))
    dp.register_message_handler(send_reserve_table, Text(equals=reply_commands.reserve_table))
    dp.register_message_handler(send_order_food, Text(equals=reply_commands.order_food))
