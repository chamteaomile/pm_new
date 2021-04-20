import asyncio  # pylint: disable=too-many-lines
import datetime
import io
import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

import aiofiles
import aiogram
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputFile, Message, ParseMode
from aiogram.utils.executor import Executor
from aiogram.utils.markdown import bold, text

from database import Admin, User, Item

from .keyboard import (
    get_kb_order, get_kb_out_links, get_kb_items_to_book, get_kb_menu_for_customer, get_kb_menu_for_admin
)


logger = logging.getLogger('telegram_bot_service')


@dataclass(frozen=True)
class TelegramBotServiceConfig:  # pylint: disable=too-many-instance-attributes
    app_name: str = 'telegram_bot'
    token: str = ''
    proxy: Optional[str] = None
    date_time_format = '%d/%m/%Y %H:%M UTC'
    date_time_format_report = '%d-%m-%Y'


default_telegram_bot_service_config = TelegramBotServiceConfig()


class Registration(StatesGroup):
    step_1 = State()


class Order(StatesGroup):
    step_1 = State()
    step_2 = State()


class TelegramBotService:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        redis_host,
        redis_port,
        redis_db,
        redis_password,
        config: TelegramBotServiceConfig = default_telegram_bot_service_config,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self._config = config
        self.loop = loop or asyncio.get_event_loop()
        self.redis_host = redis_host
        self.redis_port = int(redis_port)
        self.redis_db = int(redis_db)
        self.redis_password = redis_password
        self._storage = RedisStorage(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password
        )

        self._bot = Bot(
            token=self._config.token,
            proxy=self._config.proxy,
            loop=self.loop
        )
        self._dispatcher = Dispatcher(self._bot, loop=self.loop, storage=self._storage)
        self._executor = Executor(self._dispatcher, skip_updates=True, loop=self.loop)

    async def run_bot_task(self):
        logger.info('Bot polling started')

        self._dispatcher.register_message_handler(self._bot_start, commands=['start'])
        self._dispatcher.register_message_handler(self._show_menu, commands=['menu'], state='*')

        self._dispatcher.register_message_handler(self._registration_step_1, content_types=['text'],
                                                  state=Registration.step_1)

    async def _bot_start(self, message: Message):
        check_admin = await Admin.query.where(Admin.telegram_id == str(message.chat.id)).gino.first()
        if check_admin:
            await message.answer(f'Здравствуй, {check_admin.name}')
            await self._bot.send_message(message.chat.id, 'Введите команду /menu посмотреть список доступных функций')
            return

        check_user = await User.query.where(User.telegram_id == str(message.chat.id)).gino.first()
        if check_user:
            await message.answer(f'Здравствуйте, {check_user.name}')
            await self._bot.send_message(message.chat.id, 'Введите команду /menu посмотреть список доступных функций')

        if all([(not check_user), (not check_admin)]):
            await message.answer('Здравствуйте, мы с Вами не знакомы. \n'
                                 'Введите ваше ФИО, номер телефона, рост и вес.')
            example_registration = '\n'.join(['Пример:', 'Иванов Иван Иванович', '+79020007126', '175', '80'])
            await self._bot.send_message(
                chat_id=message.chat.id,
                text=example_registration
            )
            await Registration.step_1.set()

    async def _registration_step_1(self, message: Message, state: FSMContext):
        message_user = message.text.split('\n')
        if len(message_user) != 4:
            await message.answer('Введите как показано в примере')
            return
        name_message_user = message_user[0]
        phone_number_message_user = message_user[1]
        height_message_user = message_user[2]
        weight_message_user = message_user[3]

        new_user = await User.create(
            name=name_message_user,
            phone_number=phone_number_message_user,
            height=height_message_user,
            weight=weight_message_user,
            telegram_id=str(message.chat.id)
        )

        result = f"""
Данные успешно сохранены!
Ваше ФИО: {new_user.name}
Ваш номер телефона: {new_user.phone}
Ваш вес: {new_user.weight}
Ваш рост: {new_user.height}"""
        await self._bot.send_message(message.chat.id, result)
        await self._bot.send_message(message.chat.id, 'Введите команду /menu посмотреть список доступных функций')
        await state.finish()

    async def _show_menu(self, message: Message):
        state = self._dispatcher.current_state(user=message.chat.id)
        await state.reset_state()
        check_admin = await Admin.query.where(Admin.telegram_id == str(message.chat.id)).gino.first()
        if check_admin:
            inline_menu = await get_kb_menu_for_admin()
            await message.answer('Привет, админ. Выберите интересующий вас пункт из меню ниже:'
                                 , reply_markup=inline_menu)

        check_customer = await User.query.where(User.telegram_id == str(message.chat.id)).gino.first()
        if check_customer:
            inline_menu = await get_kb_menu_for_customer()
            await message.answer('Выберите интересующий вас пункт из меню ниже:'
                                 , reply_markup=inline_menu)

        if all([(not check_customer), (not check_admin)]):
            await message.answer('Здравствуйте, мы с Вами не знакомы. \n'
                                 'Введите ваше ФИО, номер телефона, рост и вес.')
            example_registration = '\n'.join(['Пример:', 'Иванов Иван Иванович', '+79020007126', '175', '80'])
            await self._bot.send_message(
                chat_id=message.chat.id,
                text=example_registration
            )
            await Registration.step_1.set()

    async def _show_links(self, callback_query: CallbackQuery):
        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        inline_kb = await get_kb_out_links()
        await self._bot.send_message('Мы в соцсетях!',
                                     reply_markup=inline_kb)

    async def _order_step_1(self, callback_query: CallbackQuery):
        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        inline_kb = await get_kb_items_to_book()
        await self._bot.send_message(callback_query.from_user.id, 'Выберите интересующий вас инвентарь:',
                                     reply_markup=inline_kb)
        await Order.step_1.set()

    async def _order_step_2(self, message: Message, callback_query: CallbackQuery):
        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        inline_kb = await get_kb_order()
        call = callback_query.data
        item_data = await Item.query.where(Item.data == call).gino.first()
        user_data = await User.query.where(User.telegram_id == message.chat.id).gino.first()
        user_data.order += str(call)+':'
        item_name = item_data.name
        item_price = item_data.price

        await self._bot.send_message(callback_query.from_user.id, f'Вы выбрали: {item_name}. \n'
                                                                  f'Стоимость бронирования этого инвентаря: {item_price}. \n'
                                                                  f'Хотите оформить заявку?',
                                     reply_markup=inline_kb)
        await Order.step_2.set()

    async def _order_step_3(self, callback_query: CallbackQuery, state: FSMContext):
        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)
        inline_kb = await get_kb_order()
        call = callback_query.data
        user_data = await Item.query.where(Item.data == call).gino.first()
        item_name = user_data.name
        item_price = user_data.price
        await self._bot.send_message(callback_query.from_user.id, f'Вы выбрали: {item_name}. \n'
                                                                  f'Стоимость бронирования этого инвентаря: {item_price}. \n'
                                                                  f'Хотите оформить заявку?',
                                     reply_markup=inline_kb)
        await state.finish()
