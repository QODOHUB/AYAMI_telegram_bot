from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.misc import callbacks
from tgbot.services.database.models import Group, Product, Cart, Organization
from tgbot.services.utils import generate_dates


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
            InlineKeyboardButton(product.name, callback_data=callbacks.product.new(id=product.id, action='show'))
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


def get_product_keyboard(product: Product, cart_product: Cart | None):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if cart_product:
        keyboard.add(
            InlineKeyboardButton(
                f'{product.price} * {cart_product.quantity} = {product.price * cart_product.quantity}₽',
                callback_data='pass')
        )
        keyboard.row(
            InlineKeyboardButton('🗑️', callback_data=callbacks.product.new(id=product.id, action='del')),
            InlineKeyboardButton('➖', callback_data=callbacks.product.new(id=product.id, action='-')),
            InlineKeyboardButton(str(cart_product.quantity), callback_data='pass'),
            InlineKeyboardButton('➕', callback_data=callbacks.product.new(id=product.id, action='+'))
        )
    else:
        keyboard.add(
            InlineKeyboardButton('Добавить в корзину', callback_data=callbacks.product.new(id=product.id, action='add'))
        )

    keyboard.add(
        InlineKeyboardButton('Назад', callback_data=callbacks.group.new(id=product.group_id))
    )

    return keyboard


def get_cart_keyboard(cart_products, current_product, product_num, total_sum):
    keyboard = InlineKeyboardMarkup(row_width=3)

    cart_product = cart_products[product_num - 1]
    quantity = cart_product.quantity

    keyboard.add(
        InlineKeyboardButton(f'{current_product.price} * {quantity} = {current_product.price * quantity}₽',
                             callback_data='pass')
    )
    keyboard.row(
        InlineKeyboardButton('🗑️', callback_data=callbacks.cart.new(id=cart_product.id, action='del')),
        InlineKeyboardButton('➖', callback_data=callbacks.cart.new(id=cart_product.id, action='-')),
        InlineKeyboardButton(str(quantity), callback_data='pass'),
        InlineKeyboardButton('➕', callback_data=callbacks.cart.new(id=cart_product.id, action='+'))
    )

    prev_call = callbacks.cart.new(id=cart_products[product_num - 2].id, action='show') if product_num > 1 else 'pass'
    next_call = callbacks.cart.new(id=cart_products[product_num].id, action='show') if product_num < len(cart_products) else 'pass'

    keyboard.row(
        InlineKeyboardButton('<<', callback_data=prev_call),
        InlineKeyboardButton(f'{product_num} из {len(cart_products)}', callback_data='pass'),
        InlineKeyboardButton('>>', callback_data=next_call)
    )

    keyboard.row(
        InlineKeyboardButton(f'Оформить заказ - {total_sum}₽', callback_data=callbacks.cart.new(action='pay', id=''))
    )

    return keyboard


def get_delivery_zones_keyboard(map_url, add_menu=False):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton('Открыть карту зон доставки', url=map_url)
    )

    if add_menu:
        keyboard.add(
            InlineKeyboardButton('Открыть меню', callback_data='groups')
        )

    return keyboard


def get_time_keyboard(start_time: datetime, end_time: datetime, interval: int, action):
    keyboard = InlineKeyboardMarkup(row_width=3)

    if action == 'ord':
        keyboard.row(
            InlineKeyboardButton('Как можно скорее', callback_data=callbacks.time.new(time='', action=action))
        )

    dates = generate_dates(start_time, end_time, interval)
    buttons = [InlineKeyboardButton(date.strftime('%H:%M'),
                                    callback_data=callbacks.time.new(time=date.strftime('%H-%M'), action=action)) for date in dates]
    keyboard.add(*buttons)

    return keyboard


def get_pay_keyboard(pay_url, payment_id):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton('Оплатить', url=pay_url),
        InlineKeyboardButton('Проверить оплату', callback_data=callbacks.check.new(id=payment_id))
    )

    return keyboard


def get_skip_keyboard(skip: str):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton('Пропустить', callback_data=callbacks.skip.new(value=skip))
    )

    return keyboard


def get_organizations_keyboard(organizations: list[Organization], action):
    keyboard = InlineKeyboardMarkup()

    for organization in organizations:
        keyboard.add(
            InlineKeyboardButton(organization.name_in_bot, callback_data=callbacks.organization.new(id=organization.id, action=action))
        )

    return keyboard


def get_orders_keyboard(orders_count, ind):
    keyboard = InlineKeyboardMarkup()

    prev_call = callbacks.order.new(ind=ind - 1) if ind > 0 else 'pass'
    next_call = callbacks.order.new(ind=ind + 1) if ind < orders_count - 1 else 'pass'

    keyboard.row(
        InlineKeyboardButton('<<', callback_data=prev_call),
        InlineKeyboardButton(f'{ind + 1} из {orders_count}', callback_data='pass'),
        InlineKeyboardButton('>>', callback_data=next_call)
    )

    keyboard.add(
        InlineKeyboardButton('Назад', callback_data='profile')
    )

    return keyboard


start_order = InlineKeyboardMarkup(row_width=1)
start_order.add(
    InlineKeyboardButton('На доставку', callback_data='delivery'),
    InlineKeyboardButton('Самовывоз', callback_data='pickup')
)


profile = InlineKeyboardMarkup(row_width=1)
profile.add(
    InlineKeyboardButton('Изменить имя', callback_data=callbacks.profile.new(action='update_name')),
    InlineKeyboardButton('История заказов', callback_data=callbacks.profile.new(action='show_orders'))
)

open_menu = InlineKeyboardMarkup()
open_menu.add(
    InlineKeyboardButton('Открыть меню', callback_data='groups')
)

bonuses = InlineKeyboardMarkup(row_width=1)
bonuses.add(
    InlineKeyboardButton('Не использовать баллы', callback_data='no_bonuses'),
    InlineKeyboardButton('Потратить баллы', callback_data='bonuses')
)

payment_type_choose = InlineKeyboardMarkup(row_width=1)
payment_type_choose.add(
    InlineKeyboardButton('При получении', callback_data='offline'),
    InlineKeyboardButton('Онлайн', callback_data='online')
)

continue_order = InlineKeyboardMarkup()
continue_order.add(
    InlineKeyboardButton('Продолжить', callback_data='continue')
)
