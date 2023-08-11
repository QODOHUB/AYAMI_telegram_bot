from aiogram import Dispatcher
from aiogram.types import CallbackQuery, InputMedia, InputFile, InputMediaPhoto
from aiogram.utils import markdown as md

from tgbot.keyboards import inline_keyboards
from tgbot.misc import messages, callbacks
from tgbot.services.database.models import Group, Product, TelegramUser


async def show_subgroup_or_products(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    redis = call.bot.get('redis')

    async with db() as session:
        group = await session.get(Group, callback_data['id'])
        await session.refresh(group, ['children'])
        if group.children:
            text = messages.subgroup_choose.format(group=group.name)
            keyboard = inline_keyboards.get_groups_keyboard(group.children, True)

            if call.message.photo:
                if group.image_link:
                    photo_id = await redis.get(group.image_link)
                    photo = photo_id.decode() if photo_id else InputFile.from_url(group.image_link)
                    msg = await call.message.edit_media(
                        InputMediaPhoto(photo, caption=text),
                        reply_markup=keyboard
                    )
                    if not photo_id:
                        await redis.set(group.image_link, msg.photo[-1].file_id)
                else:
                    await call.message.delete()
                    await call.message.answer(text, reply_markup=keyboard)
            else:
                if group.image_link:
                    await call.message.delete()
                    photo_id = await redis.get(group.image_link)
                    photo = photo_id.decode() if photo_id else InputFile.from_url(group.image_link)
                    msg = await call.message.answer_photo(
                        photo,
                        caption=text,
                        reply_markup=keyboard
                    )
                    if not photo_id:
                        await redis.set(group.image_link, msg.photo[-1].file_id)
                else:
                    await call.message.edit_text(text, reply_markup=keyboard)
        else:
            await session.refresh(group, ['products'])
            text = messages.product_choose.format(group=group.name)
            keyboard = inline_keyboards.get_products_keyboard(group.products, group.parent_id)

            if call.message.photo:
                if group.image_link:
                    photo_id = await redis.get(group.image_link)
                    photo = photo_id.decode() if photo_id else InputFile.from_url(group.image_link)
                    msg = await call.message.edit_media(
                        InputMediaPhoto(photo, caption=text),
                        reply_markup=keyboard
                    )
                    if not photo_id:
                        await redis.set(group.image_link, msg.photo[-1].file_id)
                else:
                    await call.message.delete()
                    await call.message.answer(text, reply_markup=keyboard)
            else:
                if group.image_link:
                    await call.message.delete()
                    photo_id = await redis.get(group.image_link)
                    photo = photo_id.decode() if photo_id else InputFile.from_url(group.image_link)
                    msg = await call.message.answer_photo(
                        photo,
                        caption=text,
                        reply_markup=keyboard
                    )
                    if not photo_id:
                        await redis.set(group.image_link, msg.photo[-1].file_id)
                else:
                    await call.message.edit_text(text, reply_markup=keyboard)

    await call.answer()


async def show_product(call: CallbackQuery, callback_data: dict):
    db = call.bot.get('database')
    redis = call.bot.get('redis')

    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        await session.refresh(tg_user.iiko_user, ['cart'])
        product = await session.get(Product, callback_data['id'])

        text = messages.product.format(name=product.name, description=product.description, price=product.price)
        keyboard = inline_keyboards.get_product_keyboard(product, tg_user.iiko_user.cart)
        if call.message.photo:
            if product.image_link:
                photo_id = await redis.get(product.image_link)
                photo = photo_id.decode() if photo_id else InputFile.from_url(product.image_link)
                msg = await call.message.edit_media(
                    InputMediaPhoto(photo, caption=text),
                    reply_markup=keyboard
                )
                if not photo_id:
                    await redis.set(product.image_link, msg.photo[-1].file_id)
            else:
                await call.message.delete()
                await call.message.answer(text, reply_markup=keyboard)
        else:
            if product.image_link:
                await call.message.delete()
                photo_id = await redis.get(product.image_link)
                photo = photo_id.decode() if photo_id else InputFile.from_url(product.image_link)
                msg = await call.message.answer_photo(
                    photo,
                    caption=text,
                    reply_markup=keyboard
                )
                if not photo_id:
                    await redis.set(product.image_link, msg.photo[-1].file_id)
            else:
                await call.message.edit_text(text, reply_markup=keyboard)

    await call.answer()


def register_menu(dp: Dispatcher):
    dp.register_callback_query_handler(show_subgroup_or_products, callbacks.group.filter())
    dp.register_callback_query_handler(show_product, callbacks.product.filter())
