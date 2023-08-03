from .commands import register_commands
from .registration import register_registration
from .main_menu import register_main_menu

register_functions = (
    register_commands,
    register_main_menu,
    register_registration
)
