from aiogram import Dispatcher
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from tgbot.keyboards import inline_keyboards
from tgbot.misc import messages, callbacks
from tgbot.services.database.models import Group, Product, TelegramUser, Cart
from tgbot.services.utils import update_message_content, update_menu_from_api


async def show_subgroup_or_products(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    redis = call.bot.get('redis')
    iiko = call.bot.get('iiko')

    async with db() as session:
        revision = await update_menu_from_api(session, iiko, redis)
        group = await session.get(Group, callback_data['id'])
        if group.revision != revision:
            await call.answer(messages.old_menu, show_alert=True)
            return

        await session.refresh(group, ['children'])
        if group.children:
            text = messages.subgroup_choose.format(group=group.name)
            revision_groups = filter(lambda grp: grp.revision == group.revision and group.show_in_bot, group.children)
            keyboard = inline_keyboards.get_groups_keyboard(revision_groups, True)
        else:
            await session.refresh(group, ['products'])
            text = messages.product_choose.format(group=group.name)
            revision_products = filter(lambda product: product.revision == group.revision and product.show_in_bot, group.products)
            keyboard = inline_keyboards.get_products_keyboard(revision_products, group.parent_id)

    await update_message_content(call, redis, text, keyboard, group.image_link)
    await call.answer()


async def show_product(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    redis = call.bot.get('redis')
    iiko = call.bot.get('iiko')

    async with db() as session:
        revision = await update_menu_from_api(session, iiko, redis)
        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        product = await session.get(Product, callback_data['id'])
        if product.revision != revision:
            await call.answer(messages.old_menu, show_alert=True)
            return

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
        cart_product = await Cart.get_user_product(session, tg_user.iiko_user.id, callback_data['id'])
        if not cart_product:
            await session.refresh(tg_user, ['iiko_user'])
            cart_product = Cart(
                iiko_user_id=tg_user.iiko_user.id,
                product_id=callback_data['id']
            )
            session.add(cart_product)
            await session.commit()

    await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, cart_product))
    await call.answer()


async def get_and_check_cart_product(call: CallbackQuery, product_id, session):
    redis = call.bot.get('redis')
    iiko = call.bot.get('iiko')
    revision = await update_menu_from_api(session, iiko, redis)
    tg_user = await session.get(TelegramUser, call.from_user.id)
    product = await session.get(Product, product_id)
    await session.refresh(tg_user, ['iiko_user'])
    cart_product = await Cart.get_user_product(session, tg_user.iiko_user.id, product_id)

    if not cart_product:
        await call.answer(messages.old_cart_product, show_alert=True)
        await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, None))
        raise CancelHandler
    if revision != product.revision:
        await call.answer(messages.old_menu, show_alert=True)
        raise CancelHandler

    return cart_product, product


async def del_from_cart(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        cart_product, product = await get_and_check_cart_product(call, callback_data['id'], session)
        await session.delete(cart_product)
        await session.commit()

    await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, None))
    await call.answer()


async def add_quantity(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        cart_product, product = await get_and_check_cart_product(call, callback_data['id'], session)
        cart_product.quantity += 1
        await session.commit()

    try:
        await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, cart_product))
    except MessageNotModified:
        pass

    await call.answer()


async def reduce_quantity(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    async with db() as session:
        cart_product, product = await get_and_check_cart_product(call, callback_data['id'], session)
        cart_product.quantity -= 1
        if cart_product.quantity == 0:
            await session.delete(cart_product)
            cart_product = None
        await session.commit()

    try:
        await call.message.edit_reply_markup(inline_keyboards.get_product_keyboard(product, cart_product))
    except MessageNotModified:
        pass

    await call.answer()


def register_menu(dp: Dispatcher):
    dp.register_callback_query_handler(show_subgroup_or_products, callbacks.group.filter())
    dp.register_callback_query_handler(show_product, callbacks.product.filter(action='show'))
    dp.register_callback_query_handler(add_to_cart, callbacks.product.filter(action='add'))
    dp.register_callback_query_handler(del_from_cart, callbacks.product.filter(action='del'))
    dp.register_callback_query_handler(add_quantity, callbacks.product.filter(action='+'))
    dp.register_callback_query_handler(reduce_quantity, callbacks.product.filter(action='-'))
