from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery, InputFile

from tgbot.keyboards import reply_keyboards, inline_keyboards
from tgbot.misc import reply_commands, messages
from tgbot.services.database.models import TelegramUser
from tgbot.services.database.models.group import Group
from tgbot.services.utils import update_menu_from_api


async def send_categories(message: Message):
    db = message.bot.get('database')
    iiko = message.bot.get('iiko')
    redis = message.bot.get('redis')

    async with db() as session:
        revision = await update_menu_from_api(session, iiko, redis)
        main_groups = await Group.get_main_groups(session, revision)

    await message.answer(messages.groups_choose, reply_markup=inline_keyboards.get_groups_keyboard(main_groups))


async def show_categories(call: CallbackQuery):
    db = call.bot.get('database')
    iiko = call.bot.get('iiko')
    redis = call.bot.get('redis')

    async with db() as session:
        revision = await update_menu_from_api(session, iiko, redis)
        main_groups = await Group.get_main_groups(session, revision)

    if call.message.photo:
        await call.message.answer(messages.groups_choose, reply_markup=inline_keyboards.get_groups_keyboard(main_groups))
        await call.message.delete()
    else:
        await call.message.edit_text(messages.groups_choose, reply_markup=inline_keyboards.get_groups_keyboard(main_groups))


async def send_cart(message: Message):
    db = message.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, message.from_id)
        await session.refresh(tg_user, ['iiko_user'])
        await session.refresh(tg_user.iiko_user, ['cart_products'])

        if not tg_user.iiko_user.cart_products:
            await message.answer(messages.empty_cart, reply_markup=inline_keyboards.open_menu)
            return

        total_sum = 0
        for ind, cart_product in enumerate(tg_user.iiko_user.cart_products):
            await session.refresh(cart_product, ['product'])
            if ind == 0:
                product_num = 1
                current_product = cart_product
            total_sum += cart_product.quantity * cart_product.product.price

        text = messages.product.format(
            name=current_product.product.name,
            price=current_product.product.price,
            description=current_product.product.description
        )
        keyboard = inline_keyboards.get_cart_keyboard(tg_user.iiko_user.cart_products, current_product.product,
                                                      product_num, total_sum)

        if current_product.product.image_link:
            redis = message.bot.get('redis')
            photo_id = await redis.get(current_product.product.image_link)
            photo = photo_id.decode() if photo_id else InputFile.from_url(current_product.product.image_link)
            await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)


async def send_main_menu(message: Message):
    await message.answer(messages.main_menu, reply_markup=reply_keyboards.main_menu)


def register_order_menu(dp: Dispatcher):
    dp.register_message_handler(send_categories, Text(equals=reply_commands.open_menu))
    dp.register_message_handler(send_cart, Text(equals=reply_commands.cart))
    dp.register_message_handler(send_main_menu, Text(equals=reply_commands.main_menu))
    dp.register_callback_query_handler(show_categories, text='groups')
