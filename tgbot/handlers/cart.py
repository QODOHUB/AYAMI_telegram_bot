from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, InputFile, InputMediaPhoto

from tgbot.keyboards import inline_keyboards
from tgbot.misc import messages, callbacks
from tgbot.services.database.models import TelegramUser, Cart
from tgbot.services.utils import update_message_content


async def show_cart_product(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        current_product = await session.get(Cart, int(callback_data['id']))
        if not current_product:
            await call.answer(messages.request_new_cart, show_alert=True)
            return
        await session.refresh(current_product, ['iiko_user'])
        await session.refresh(current_product.iiko_user, ['cart_products'])

        total_sum = 0
        for ind, cart_product in enumerate(current_product.iiko_user.cart_products):
            await session.refresh(cart_product, ['product'])
            if current_product.id == cart_product.id:
                product_num = ind + 1
            total_sum += cart_product.quantity * cart_product.product.price

        text = messages.product.format(
            name=current_product.product.name,
            price=current_product.product.price,
            description=current_product.product.description
        )
        keyboard = inline_keyboards.get_cart_keyboard(current_product.iiko_user.cart_products, current_product.product,
                                                      product_num, total_sum)

    redis = call.bot.get('redis')
    await update_message_content(call, redis, text, keyboard, current_product.product.image_link)

    await call.answer()


async def add_quantity(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')

    async with db() as session:
        cart_product = await session.get(Cart, int(callback_data['id']))
        if not cart_product:
            await call.answer(messages.request_new_cart, show_alert=True)
            return
        cart_product.quantity += 1
        await session.refresh(cart_product, ['iiko_user'])
        iiko_user = cart_product.iiko_user
        await session.refresh(iiko_user, ['cart_products'])
        await session.commit()

        total_sum = 0
        for ind, product in enumerate(iiko_user.cart_products):
            await session.refresh(product, ['product'])
            if product.id == int(callback_data['id']):
                product_num = ind + 1

            total_sum += product.quantity * product.product.price

        await call.message.edit_reply_markup(inline_keyboards.get_cart_keyboard(
            iiko_user.cart_products,
            cart_product.product,
            product_num,
            total_sum
        ))

    await call.answer()


async def reduce_quantity(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')

    async with db() as session:
        cart_product = await session.get(Cart, int(callback_data['id']))
        if not cart_product:
            await call.answer(messages.request_new_cart, show_alert=True)
            return
        cart_product.quantity -= 1
        await session.refresh(cart_product, ['iiko_user'])
        iiko_user = cart_product.iiko_user
        await session.commit()
        await session.refresh(iiko_user, ['cart_products'])

        if cart_product.quantity == 0:
            await session.delete(cart_product)
            await session.commit()
            if len(iiko_user.cart_products) == 1:
                await call.message.delete()
                await call.message.answer(messages.empty_cart, reply_markup=inline_keyboards.open_menu)
                await call.answer()
            else:
                await session.refresh(iiko_user, ['cart_products'])
                await show_cart_product(call, callback_data={'id': iiko_user.cart_products[0].id})
            return

        total_sum = 0
        for ind, product in enumerate(iiko_user.cart_products):
            await session.refresh(product, ['product'])
            if product.id == int(callback_data['id']):
                product_num = ind + 1

            total_sum += product.quantity * product.product.price

        await call.message.edit_reply_markup(inline_keyboards.get_cart_keyboard(
            iiko_user.cart_products,
            cart_product.product,
            product_num,
            total_sum
        ))

    await call.answer()


async def del_product(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')

    async with db() as session:
        cart_product = await session.get(Cart, int(callback_data['id']))
        if not cart_product:
            await call.answer(messages.request_new_cart, show_alert=True)
            return
        await session.refresh(cart_product, ['iiko_user'])
        await session.refresh(cart_product.iiko_user, ['cart_products'])
        await session.delete(cart_product)
        await session.commit()

        if len(cart_product.iiko_user.cart_products) == 1:
            await call.message.delete()
            await call.message.answer(messages.empty_cart, reply_markup=inline_keyboards.open_menu)
            return

        await session.refresh(cart_product.iiko_user, ['cart_products'])
        await show_cart_product(call, callback_data={'id': cart_product.iiko_user.cart_products[0].id})


async def start_order(call: CallbackQuery, callback_data: dict):
    await call.answer('В разработке', show_alert=True)


def register_cart(dp: Dispatcher):
    dp.register_callback_query_handler(show_cart_product, callbacks.cart.filter(action='show'))
    dp.register_callback_query_handler(del_product, callbacks.cart.filter(action='del'))
    dp.register_callback_query_handler(start_order, callbacks.cart.filter(action='pay'))
    dp.register_callback_query_handler(add_quantity, callbacks.cart.filter(action='+'))
    dp.register_callback_query_handler(reduce_quantity, callbacks.cart.filter(action='-'))
