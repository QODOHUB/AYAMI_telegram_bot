from .commands import register_commands
from .registration import register_registration
from .main_menu import register_main_menu
from .profile import register_profile
from .other import register_other
from .order_menu import register_order_menu
from .menu import register_menu
from .cart import register_cart
from .order import register_order
from .reserve import register_reserve
from .admin import register_admin

register_functions = (
    register_commands,
    register_main_menu,
    register_registration,
    register_other,
    register_profile,
    register_order_menu,
    register_menu,
    register_cart,
    register_order,
    register_reserve,
    register_admin
)
