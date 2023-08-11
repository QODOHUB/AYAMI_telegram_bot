from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.misc import callbacks
from tgbot.services.database.models import Group, Product, Cart


def get_feedback_keyboard(feedback_url: str):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton('📋 Заполнить форму', url=feedback_url))

    return keyboard


def get_groups_keyboard(groups: list[Group], back=False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for group in groups:
        keyboard.add(
            InlineKeyboardButton(group.name, callback_data=callbacks.group.new(id=group.id))
        )

    if back:
        keyboard.add(
            InlineKeyboardButton('Назад', callback_data='groups')
        )

    return keyboard


def get_products_keyboard(products: list[Product], back_group_id):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for product in products:
        keyboard.add(
            InlineKeyboardButton(product.name, callback_data=callbacks.product.new(id=product.id))
        )

    if back_group_id:
        keyboard.add(
            InlineKeyboardButton('Назад', callback_data=callbacks.group.new(id=back_group_id))
        )
    else:
        keyboard.add(
            InlineKeyboardButton('Назад', callback_data='groups')
        )

    return keyboard


def get_product_keyboard(product: Product, cart: Cart):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton('Назад', callback_data=callbacks.group.new(id=product.group_id))
    )

    return keyboard


profile = InlineKeyboardMarkup(row_width=1)
profile.add(
    InlineKeyboardButton('Изменить имя', callback_data=callbacks.profile.new(action='update_name')),
    InlineKeyboardButton('История заказов', callback_data=callbacks.profile.new(action='show_orders'))
)
