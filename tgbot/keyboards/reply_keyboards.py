from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from tgbot.misc import reply_commands


main_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
main_menu.add(
    KeyboardButton(reply_commands.order_food),
    KeyboardButton(reply_commands.reserve_table),
    KeyboardButton(reply_commands.feedback),
    KeyboardButton(reply_commands.account)
)

request_contact = ReplyKeyboardMarkup(resize_keyboard=True)
request_contact.add(KeyboardButton(reply_commands.share_phone, request_contact=True))

cancel = ReplyKeyboardMarkup(resize_keyboard=True)
cancel.add(KeyboardButton(reply_commands.cancel))

order = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
order.add(
    KeyboardButton(reply_commands.open_menu),
    KeyboardButton(reply_commands.cart),
    KeyboardButton(reply_commands.delivery_zones),
    KeyboardButton(reply_commands.main_menu)
)
