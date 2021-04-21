import asyncio
import logging

from config import Config
from database import db
from telegram_bot import TelegramBotService


async def main(config: Config, loop: asyncio.AbstractEventLoop):  # pylint: disable=too-many-locals
    logging.info('%s started', config.app_name)
    logging.debug('Open PostgreSQL connection %s', config.pg_connection)
    await db.set_bind(config.pg_connection, loop=loop)
    pass_host, port_db = (config.redis_connection[config.redis_connection.find(":") + 4:]).split(':')
    redis_password, redis_host = pass_host.split('@')
    redis_port, redis_db = port_db.split('/')
    telegram_bot_service = TelegramBotService(
        redis_host=redis_host,
        redis_port=redis_port,
        redis_db=redis_db,
        redis_password=redis_password,
        config=config.telegram_bot_service_config,
        loop=loop
    )
    loop.create_task(telegram_bot_service.run_bot_task())
