import re
from pprint import pprint

from aiogram.types import InputFile, InputMediaPhoto

from tgbot.services.database.models.group import Group
from tgbot.services.database.models.product import Product


def contains_only_russian_letters(input_string):
    pattern = r'^[а-яА-ЯёЁ]+$'
    return bool(re.match(pattern, input_string))


async def update_menu_from_api(session, iiko, redis):
    revision = int(await redis.get('revision'))

    menu = await iiko.get_menu(start_revision=revision)
    if not menu.products:
        return

    added_groups = set()
    for group in menu.groups:
        if group.isDeleted or not group.isIncludedInMenu or group.isGroupModifier:
            continue

        db_group = await session.get(Group, group.id)
        if db_group:
            db_group.image_link = group.imageLinks[0] if group.imageLinks and 'http' in group.imageLinks[0] else None
            db_group.name = group.name
            db_group.revision = menu.revision
            db_group.parent_id = group.parentGroup
        else:

            new_group = Group(
                id=group.id,
                image_link=group.imageLinks[0] if group.imageLinks and 'http' in group.imageLinks[0] else None,
                name=group.name,
                revision=menu.revision,
                parent_id=group.parentGroup
            )
            session.add(new_group)
        added_groups.add(group.id)

    added = set()
    bad_groups = set()
    for product in menu.products:
        if product.isDeleted or product.type != 'Dish' or product.code in added or 'Доставка' in product.name:
            continue

        if product.groupId in added_groups:
            group_id = product.groupId
        else:
            bad_groups.add(product.groupId)
            group_id = product.parentGroup

        db_product = await session.get(Product, product.id)
        if db_product:
            db_product.image_link = product.imageLinks[0] if product.imageLinks and 'http' in product.imageLinks[0] else None
            db_product.name = product.name
            db_product.description = product.description
            db_product.price = product.sizePrices[0].price.currentPrice
            db_product.revision = menu.revision
            db_product.group_id = group_id
        else:
            new_product = Product(
                id=product.id,
                image_link=product.imageLinks[0] if product.imageLinks and 'http' in product.imageLinks[0] else None,
                name=product.name,
                description=product.description,
                price=product.sizePrices[0].price.currentPrice,
                revision=menu.revision,
                group_id=group_id
            )
            session.add(new_product)
        added.add(product.code)

    await session.commit()
    await redis.set('revision', menu.revision)


async def update_message_content(call, redis, text, keyboard, image_link):
    if call.message.photo:
        if image_link:
            photo_id = await redis.get(image_link)
            photo = photo_id.decode() if photo_id else InputFile.from_url(image_link)
            msg = await call.message.edit_media(InputMediaPhoto(photo, caption=text), reply_markup=keyboard)
            if not photo_id:
                await redis.set(image_link, msg.photo[-1].file_id)
        else:
            await call.message.delete()
            await call.message.answer(text, reply_markup=keyboard)
    else:
        if image_link:
            photo_id = await redis.get(image_link)
            photo = photo_id.decode() if photo_id else InputFile.from_url(image_link)
            msg = await call.message.answer_photo(photo, caption=text, reply_markup=keyboard)
            await call.message.delete()
            if not photo_id:
                await redis.set(image_link, msg.photo[-1].file_id)
        else:
            await call.message.edit_text(text, reply_markup=keyboard)
