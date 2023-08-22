from aiogram.utils.callback_data import CallbackData


# actions: 'update_name', 'show_orders'
profile = CallbackData('profile', 'action')

group = CallbackData('grp', 'id')

# actions: 'add', 'del', '+', '-'
product = CallbackData('prd', 'action', 'id')

# actions: 'del', '+', '-', 'pay', 'show'
cart = CallbackData('crt', 'action', 'id')

time = CallbackData('time', 'time')

check = CallbackData('check', 'id')

skip = CallbackData('skip', 'value')

organization = CallbackData('org', 'id')

order = CallbackData('order', 'ind')
