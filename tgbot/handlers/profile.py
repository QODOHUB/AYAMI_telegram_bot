import pytz
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.handlers.main_menu import send_profile
from tgbot.keyboards import reply_keyboards, inline_keyboards
from tgbot.misc import callbacks, states, messages
from tgbot.services.database.models import IikoUser, TelegramUser
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
    db = call.bot.get('database')
    async with db() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, call.from_user.id)
        await session.refresh(iiko_user, ['orders'])

        if not iiko_user.orders:
            await call.answer('У вас пока нет заказов!', show_alert=True)
        else:
            await show_order(call, {'ind': 0})


async def show_order(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, call.from_user.id)
        await session.refresh(iiko_user, ['orders'])
        cur_order = iiko_user.orders[int(callback_data['ind'])]
        await session.refresh(cur_order, ['order_products'])
        products_str = ''
        for order_product in cur_order.order_products:
            product = order_product.product
            price = product.price * order_product.quantity
            products_str += f'- {product.name}: {product.price}₽ * {order_product.quantity} = {price}₽\n'

    if cur_order.type == 'delivery':
        order_type = 'Доставка'
        delivery = f'\nДоставка: {cur_order.delivery}₽'
    else:
        order_type = 'Самовывоз'
        delivery = ''

    order_time = cur_order.created_at.astimezone(pytz.timezone('Europe/Moscow'))

    text = messages.order.format(
        date=order_time.strftime('%Y-%m-%d %H:%M'),
        type=order_type,
        payment_sum=f'{cur_order.payment_sum}₽ + {cur_order.bonus_pay} бон. = {cur_order.payment_sum + cur_order.bonus_pay}',
        delivery=delivery,
        order_list=products_str
    )

    keyboard = inline_keyboards.get_orders_keyboard(len(iiko_user.orders), int(callback_data['ind']))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


def register_profile(dp: Dispatcher):
    dp.register_callback_query_handler(start_name_update, callbacks.profile.filter(action='update_name'))
    dp.register_message_handler(get_new_name, state=states.UpdateName.waiting_for_name)

    dp.register_callback_query_handler(show_orders, callbacks.profile.filter(action='show_orders'))
    dp.register_callback_query_handler(show_order, callbacks.order.filter())
