from aiogram import Dispatcher
from aiogram.types import Message

from tgbot.keyboards import reply_keyboards
from tgbot.misc import messages, states
from tgbot.services.database.models import TelegramUser


async def command_start(message: Message):
    db = message.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, message.from_id)
        if tg_user is None:
            tg_user = TelegramUser(
                telegram_id=message.from_id,
                mention=message.from_user.mention,
                full_name=message.from_user.full_name
            )
            session.add(tg_user)
            await session.commit()

        await session.refresh(tg_user, ['iiko_user'])

    if not tg_user.iiko_user:
        await message.answer(messages.start, reply_markup=reply_keyboards.request_contact)
        await states.Registration.first()
    else:
        await message.answer('Главное меню', reply_markup=reply_keyboards.main_menu)


def register_commands(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
