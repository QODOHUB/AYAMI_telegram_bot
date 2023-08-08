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
class IikoConfig:
    login: str
    default_organization_id: str


@dataclass
class Config:
    bot: TelegramBot
    database: DatabaseConfig
    misc: Miscellaneous
    iiko: IikoConfig


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
        )
    )
