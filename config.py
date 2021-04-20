import os
from dataclasses import dataclass, field
from typing import Dict

import toml

from telegram_bot import TelegramBotServiceConfig, default_telegram_bot_service_config


app_root = os.path.abspath(os.path.dirname(__file__))
pyproject_info = toml.load(os.path.join(app_root, 'pyproject.toml'))
poetry_info = pyproject_info['tool']['poetry']

app_name = poetry_info['name']
app_version = poetry_info['version']
default_input_exchange = app_name
default_output_exchange = app_name


def logging_params(debug: bool = False) -> Dict:
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {'standard': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'}},
        'handlers': {'default': {'formatter': 'standard', 'class': 'logging.StreamHandler'}},
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO' if not debug else 'DEBUG',
                'propagate': True
            },
            'aiogram': {'level': 'ERROR'},
            'gino': {'level': 'ERROR'},
            'ddtrace': {'level': 'CRITICAL'}
        }
    }


@dataclass(frozen=True)
class Config:  # pylint: disable=too-many-instance-attributes
    pg_connection: str
    redis_connection: str

    telegram_bot_service_config: TelegramBotServiceConfig = default_telegram_bot_service_config

    app_name: str = app_name
    app_version: str = app_version
    logging_params: Dict = field(default_factory=logging_params)

    ddtrace_hostname: str = 'localhost'

    develop: bool = True
    debug: bool = False
    docker: bool = False
    environment: str = 'production'
