from aiogram.utils.callback_data import CallbackData


# actions: 'update_name', 'show_orders'
profile = CallbackData('profile', 'action')

group = CallbackData('grp', 'id')

# actions: 'add', 'del', '+', '-'
product = CallbackData('prd', 'action', 'id')

# actions: 'del', '+', '-', 'pay', 'show'
cart = CallbackData('crt', 'action', 'id')

# actions: 'ord', 'res'
time = CallbackData('time', 'time', 'action')

check = CallbackData('check', 'id')

skip = CallbackData('skip', 'value')

# actions: 'ord', 'res'
organization = CallbackData('org', 'id', 'action')

order = CallbackData('order', 'ind')
