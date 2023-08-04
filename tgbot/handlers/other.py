from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message

from tgbot.keyboards import reply_keyboards
from tgbot.misc import reply_commands, messages


async def cancel(message: Message, state: FSMContext):
    await message.answer(messages.main_menu, reply_markup=reply_keyboards.main_menu)
    await state.finish()


def register_other(dp: Dispatcher):
    dp.register_message_handler(cancel, Text(equals=reply_commands.cancel), state='*')
