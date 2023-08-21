import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram.types import InputFile, InputMediaPhoto

from tgbot.services.database.models import Organization, IikoUser
from tgbot.services.database.models.group import Group
from tgbot.services.database.models.product import Product
from tgbot.services.iiko.api import Iiko


def contains_only_russian_letters(input_string):
    pattern = r'^[а-яА-ЯёЁ]+$'
    return bool(re.match(pattern, input_string))


async def update_organizations_from_api(session, iiko: Iiko):
    organizations = await iiko.get_organizations(extended_info=True, include_disabled=False)
    for organization in organizations.organizations:
        db_org = await session.get(Organization, organization.id)
        if db_org:
            db_org.name = organization.name
            db_org.code = organization.code
            db_org.address = organization.restaurantAddress
        else:
            new_db_org = Organization(
                id=organization.id,
                name=organization.name,
                code=organization.code,
                address=organization.restaurantAddress,
                name_in_bot=organization.restaurantAddress
            )
            session.add(new_db_org)

    await session.commit()


async def update_user_from_api(session, iiko: Iiko, user_id) -> IikoUser:
    user = await iiko.get_customer_info('id', str(user_id))
    db_user = await session.get(IikoUser, user_id)
    db_user.referrer_id = user.referrerId
    db_user.name = user.name
    db_user.surname = user.surname
    db_user.middle_name = user.middleName
    db_user.comment = user.comment
    db_user.culture_name = user.cultureName
    db_user.birthday = user.birthday
    db_user.email = user.email
    db_user.sex = user.sex
    db_user.bonus_balance = user.walletBalances[0].balance
    await session.commit()
    return db_user


async def update_menu_from_api(session, iiko, redis):
    revision = int(await redis.get('revision'))

    menu = await iiko.get_menu(start_revision=revision)
    if not menu.products:
        return revision

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
        if product.isDeleted or product.type != 'Dish' or product.code in added:
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
    return menu.revision


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


def round_up_to_interval(date, interval):
    remainder = (date - datetime.min) % interval
    if remainder:
        return date + (interval - remainder)
    return date


def generate_dates(start_date: datetime, end_date: datetime, interval_minutes: int):
    interval = timedelta(minutes=interval_minutes)

    start_date = round_up_to_interval(start_date, interval)
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += interval


def check_time(time: datetime):
    current_time = datetime.now()
