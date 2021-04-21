import asyncio
import logging
import logging.config
import aioredis
import signal
from typing import Dict

import click

import app
from config import Config, app_name, logging_params
from telegram_bot import TelegramBotServiceConfig


def stop_loop(loop: asyncio.AbstractEventLoop):
    loop.stop()


def exception_handler(loop: asyncio.AbstractEventLoop, context: Dict):
    loop.default_exception_handler(context)
    stop_loop(loop)


@click.command()
@click.option('--environment', envvar='ENVIRONMENT', type=str, default='production', help='Sentry environment')
@click.option('--docker', envvar='IS_DOCKER', is_flag=True, default=False, help='Docker режим')
@click.option('--debug', envvar='DEBUG', is_flag=True, default=False, help='Debug режим')
@click.option('--develop', envvar='DEVELOP', is_flag=True, default=True, help='Develop режим')
@click.option('--telegram_bot_proxy', envvar='TELEGRAM_BOT_PROXY', type=str, default=None, help='Telegram Proxy')
@click.argument('telegram_bot_token', envvar='TELEGRAM_BOT_TOKEN', type=str)
@click.argument('pg_connection', envvar='PG_CONNECTION', type=str)
@click.argument('redis_connection', envvar='REDIS_CONNECTION', type=str)
def main(
    environment: str,
    docker: bool,
    debug: bool,
    develop: bool,
    telegram_bot_proxy: str,
    telegram_bot_token: str,
    pg_connection: str,
    redis_connection: str
):
    config = Config(
        pg_connection=pg_connection,
        redis_connection=redis_connection,
        telegram_bot_service_config=TelegramBotServiceConfig(
            app_name=app_name,
            token=telegram_bot_token,
            proxy=telegram_bot_proxy
        ),
        logging_params=logging_params(debug),
        develop=develop,
        debug=debug,
        docker=docker,
        environment=environment
    )

    logging.config.dictConfig(config.logging_params)

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_loop, loop)

    loop.create_task(app.main(config, loop))
    loop.run_forever()


if __name__ == '__main__':
    main()
