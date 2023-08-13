from aiogram import Dispatcher
from aiogram.types import CallbackQuery, InputMedia, InputFile, InputMediaPhoto
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards
from tgbot.misc import messages, callbacks
from tgbot.services.database.models import Group, Product, TelegramUser, Cart
from tgbot.services.utils import update_message_content


async def show_subgroup_or_products(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    redis = call.bot.get('redis')

    async with db() as session:
        group = await session.get(Group, callback_data['id'])
        await session.refresh(group, ['children'])
        if group.children:
            text = messages.subgroup_choose.format(group=group.name)
            keyboard = inline_keyboards.get_groups_keyboard(group.children, True)
        else:
            await session.refresh(group, ['products'])
            text = messages.product_choose.format(group=group.name)
            keyboard = inline_keyboards.get_products_keyboard(group.products, group.parent_id)

    await update_message_content(call, redis, text, keyboard, group.image_link)
    await call.answer()


async def show_product(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    redis = call.bot.get('redis')

    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        product = await session.get(Product, callback_data['id'])

        text = messages.product.format(name=product.name, description=product.description, price=product.price)
        cart_product = await Cart.get_user_product(session, tg_user.iiko_user.id, callback_data['id'])
        keyboard = inline_keyboards.get_product_keyboard(product, cart_product)

    await update_message_content(call, redis, text, keyboard, product.image_link)
    await call.answer()


async def add_to_cart(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        product = await session.get(Product, callback_data['id'])
        await session.refresh(tg_user, ['iiko_user'])
        new_cart_product = Cart(
            iiko_user_id=tg_user.iiko_user.id,
            product_id=callback_data['id']
        )
        session.add(new_cart_product)
        await session.commit()

    await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, new_cart_product))
    await call.answer()


async def del_from_cart(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        product = await session.get(Product, callback_data['id'])
        await session.refresh(tg_user, ['iiko_user'])
        cart_product = await Cart.get_user_product(session, tg_user.iiko_user.id, callback_data['id'])
        await session.delete(cart_product)
        await session.commit()

    await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, None))
    await call.answer()


async def add_quantity(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        product = await session.get(Product, callback_data['id'])
        await session.refresh(tg_user, ['iiko_user'])
        cart_product = await Cart.get_user_product(session, tg_user.iiko_user.id, callback_data['id'])
        cart_product.quantity += 1
        await session.commit()

    await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, cart_product))
    await call.answer()


async def reduce_quantity(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        product = await session.get(Product, callback_data['id'])
        await session.refresh(tg_user, ['iiko_user'])
        cart_product = await Cart.get_user_product(session, tg_user.iiko_user.id, callback_data['id'])
        cart_product.quantity -= 1
        if cart_product.quantity == 0:
            await session.delete(cart_product)
            cart_product = None
        await session.commit()

    await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, cart_product))
    await call.answer()


def register_menu(dp: Dispatcher):
    dp.register_callback_query_handler(show_subgroup_or_products, callbacks.group.filter())
    dp.register_callback_query_handler(show_product, callbacks.product.filter(action='show'))
    dp.register_callback_query_handler(add_to_cart, callbacks.product.filter(action='add'))
    dp.register_callback_query_handler(del_from_cart, callbacks.product.filter(action='del'))
    dp.register_callback_query_handler(add_quantity, callbacks.product.filter(action='+'))
    dp.register_callback_query_handler(reduce_quantity, callbacks.product.filter(action='-'))
