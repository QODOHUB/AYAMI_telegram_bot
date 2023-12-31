import asyncio
import datetime
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aioredis import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from yookassa import Configuration

from tgbot.config import load_config
from tgbot import handlers
from tgbot import filters
from tgbot import middlewares
from tgbot.services.database.base import Base
from tgbot.services.iiko.api import Iiko

logger = logging.getLogger(__name__)


def register_all_middlewares(dp, config):
    dp.setup_middleware(middlewares.EnvironmentMiddleware(config=config))
    # dp.setup_middleware(middlewares.ThrottlingMiddleware())
    dp.setup_middleware(middlewares.AlbumMiddleware())


def register_all_filters(dp):
    for aiogram_filter in filters.filters:
        dp.filters_factory.bind(aiogram_filter)


def register_all_handlers(dp):
    for register in handlers.register_functions:
        register(dp)


async def main():
    config = load_config('.env')
    logging_handlers = [logging.StreamHandler()]
    if config.bot.write_logs:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        log_file = rf'logs/{datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")}.log'
        logging_handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
        handlers=logging_handlers
    )
    logger.info('Starting bot')

    bot = Bot(token=config.bot.token, parse_mode='HTML')
    bot_info = await bot.me
    logger.info(f'Bot: {bot_info.username} [{bot_info.mention}]')

    storage = RedisStorage2(host='localhost')
    dp = Dispatcher(bot, storage=storage)
    redis = Redis(host='localhost')

    engine = create_async_engine(
        f'postgresql+asyncpg://{config.database.user}:{config.database.password}@127.0.0.1/{config.database.database}',
        future=True
    )
    async_sessionmaker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession, future=True)

    iiko = Iiko(config.iiko.login, config.iiko.default_organization_id)

    Configuration.account_id = config.yookassa.store_id
    Configuration.secret_key = config.yookassa.secret_key

    bot['config'] = config
    bot['redis'] = redis
    bot['database'] = async_sessionmaker
    bot['iiko'] = iiko

    register_all_middlewares(dp, config)
    register_all_filters(dp)
    register_all_handlers(dp)

    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()

        bot_session = await bot.get_session()
        await bot_session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error('Bot stopped!')
        raise e
