from aiogram import Dispatcher
from aiogram.types import CallbackQuery, InputMedia, InputFile
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards
from tgbot.misc import messages, callbacks
from tgbot.services.database.models import Group, Product


async def show_subgroup_or_products(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')

    async with db() as session:
        group = await session.get(Group, callback_data['id'])
        await session.refresh(group, ['children'])
        if group.children:
            await call.message.edit_text(
                messages.subgroup_choose.format(group=group.name) + md.hide_link(group.image_link),
                reply_markup=inline_keyboards.get_groups_keyboard(group.children, True)
            )
        else:
            await session.refresh(group, ['products'])
            await call.message.edit_text(
                messages.product_choose.format(group=group.name) + md.hide_link(group.image_link),
                reply_markup=inline_keyboards.get_products_keyboard(group.products)
            )

    await call.answer()


async def show_product(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')

    async with db() as session:
        product = await session.get(Product, callback_data['id'])

        text = messages.product.format(name=product.name, description=product.description, price=product.price) + '\n' + md.hide_link(product.image_link)
        print(text)
        await call.message.edit_text(
            text
        )

    await call.answer()


def register_menu(dp: Dispatcher):
    dp.register_callback_query_handler(show_subgroup_or_products, callbacks.group.filter())
    dp.register_callback_query_handler(show_product, callbacks.product.filter())
