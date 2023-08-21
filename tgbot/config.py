from dataclasses import dataclass

from environs import Env


@dataclass
class DatabaseConfig:
    password: str
    user: str
    database: str


@dataclass
class TelegramBot:
    token: str
    admin_ids: list[int]
    write_logs: bool


@dataclass
class Miscellaneous:
    feedback_url: str


@dataclass
class IikoPayments:
    cash: str
    courier: str
    bonuses: str
    visa: str
    online: str


@dataclass
class IikoConfig:
    login: str
    default_organization_id: str
    map_url: str
    payments: IikoPayments


@dataclass
class YooKassa:
    secret_key: str
    store_id: str
    redirect_url: str


@dataclass
class Config:
    bot: TelegramBot
    database: DatabaseConfig
    misc: Miscellaneous
    iiko: IikoConfig
    yookassa: YooKassa


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        bot=TelegramBot(
            token=env.str('BOT_TOKEN'),
            admin_ids=list(map(int, env.list('ADMINS'))),
            write_logs=env.bool('WRITE_LOGS'),
        ),
        database=DatabaseConfig(
            password=env.str('POSTGRES_PASSWORD'),
            user=env.str('POSTGRES_USER'),
            database=env.str('POSTGRES_DB')
        ),
        misc=Miscellaneous(
            feedback_url=env.str('FEEDBACK_URL'),

        ),
        iiko=IikoConfig(
            login=env.str('IIKO_LOGIN'),
            default_organization_id=env.str('DEFAULT_ORGANIZATION'),
            map_url=env.str('MAP_URL'),
            payments=IikoPayments(
                cash=env.str('CASH'),
                courier=env.str('COURIER'),
                bonuses=env.str('BONUSES'),
                visa=env.str('VISA'),
                online=env.str('ONLINE')
            )
        ),
        yookassa=YooKassa(
            secret_key=env.str('YOOKASSA_KEY'),
            store_id=env.str('YOOKASSA_STORE_ID'),
            redirect_url=env.str('REDIRECT_URL')
        )
    )
