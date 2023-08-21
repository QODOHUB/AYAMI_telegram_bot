from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery

from tgbot.keyboards import reply_keyboards
from tgbot.misc import reply_commands, messages
from tgbot.misc.states import Order


async def cancel(message: Message, state: FSMContext):
    if await state.get_state() in Order:
        await message.answer(messages.order_food, reply_markup=reply_keyboards.order)
    else:
        await message.answer(messages.main_menu, reply_markup=reply_keyboards.main_menu)
    await state.finish()


async def pass_call(call: CallbackQuery):
    await call.answer()


def register_other(dp: Dispatcher):
    dp.register_message_handler(cancel, Text(equals=reply_commands.cancel), state='*')
    dp.register_callback_query_handler(pass_call, text='pass')
