import asyncio
import logging
import logging.config
import signal
from typing import Dict

import click
import msgpack
import msgpack_numpy
from ddtrace import tracer
from ddtrace.contrib.asyncio import context_provider

import app
from config import Config, app_name, logging_params
from telegram_bot import TelegramBotServiceConfig


def stop_loop(loop: asyncio.AbstractEventLoop):
    loop.stop()


def exception_handler(loop: asyncio.AbstractEventLoop, context: Dict):
    loop.default_exception_handler(context)
    stop_loop(loop)


@click.command()
@click.option('--environment', envvar='ENVIRONMENT', type=str, default='production', help='Sentry environment')  # noqa
@click.option('--docker', envvar='IS_DOCKER', is_flag=True, default=False, help='Docker режим')  # noqa
@click.option('--debug', envvar='DEBUG', is_flag=True, default=False, help='Debug режим')  # noqa
@click.option('--develop', envvar='DEVELOP', is_flag=True, default=True, help='Develop режим')  # noqa
@click.option('--ddtrace_hostname', envvar='DATADOG_TRACE_AGENT_HOSTNAME', type=str, default='localhost', help='DataDog tracer hostname')  # noqa
@click.option('--telegram_bot_proxy', envvar='TELEGRAM_BOT_PROXY', type=str, default=None, help='Telegram Proxy')  # noqa
@click.argument('telegram_bot_token', envvar='TELEGRAM_BOT_TOKEN', type=str)  # noqa
@click.argument('pg_connection', envvar='PG_CONNECTION', type=str)  # noqa
@click.argument('redis_connetion', envvar='REDIS_CONNECTION', type=str)  # noqa
def main(  # pylint: disable=too-many-arguments,too-many-locals
    environment: str,
    docker: bool,
    debug: bool,
    develop: bool,
    ddtrace_hostname: str,
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
        ddtrace_hostname=ddtrace_hostname,
        develop=develop,
        debug=debug,
        docker=docker,
        environment=environment
    )

    logging.config.dictConfig(config.logging_params)
    tracer.configure(hostname=config.ddtrace_hostname, context_provider=context_provider)
    msgpack_numpy.patch()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_loop, loop)

    loop.create_task(app.main(config, loop))
    loop.run_forever()


if __name__ == '__main__':
    main()