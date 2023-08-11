from aiogram.utils.callback_data import CallbackData


# actions: 'update_name', 'show_orders'
profile = CallbackData('profile', 'action')

group = CallbackData('grp', 'id')

# actions: 'add', 'del', '+', '-'
product = CallbackData('prd', 'action', 'id')

# actions: 'add', 'del', '+', '-', 'pay'
cart = CallbackData('crt', 'action', 'id')
