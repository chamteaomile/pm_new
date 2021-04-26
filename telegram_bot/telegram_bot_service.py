import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.executor import Executor

from database import Admin, User, Item, Order

from .keyboard import (
    get_kb_order, get_kb_out_links, get_kb_menu_for_customer, get_kb_menu_for_admin,
    get_kb_category, get_kb_subcategory, get_kb_time, get_kb_edit_menu, translation
)
from .prices_api import new_db


logger = logging.getLogger('telegram_bot_service')


@dataclass(frozen=True)
class TelegramBotServiceConfig:
    app_name: str = 'telegram_bot'
    token: str = ''
    proxy: Optional[str] = None
    date_time_format = '%d/%m/%Y %H:%M UTC'
    date_time_format_report = '%d-%m-%Y'


default_telegram_bot_service_config = TelegramBotServiceConfig()


class Registration(StatesGroup):
    step_1 = State()


class Edit(StatesGroup):
    step_1 = State()
    step_name = State()
    step_phone_number = State()
    step_height = State()
    step_weight = State()


class Book(StatesGroup):
    step_1 = State()
    step_2 = State()
    step_3 = State()
    step_4 = State()


class TelegramBotService:
    def __init__(
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

        self._dispatcher.register_message_handler(self._registration_step_1, state=Registration.step_1)

        self._dispatcher.register_callback_query_handler(self._show_links, text='links')
        self._dispatcher.register_callback_query_handler(self._book, text='book')
        self._dispatcher.register_callback_query_handler(self._edit, text='edit')

        self._dispatcher.register_callback_query_handler(self._update_db, text='update_db')
        self._dispatcher.register_callback_query_handler(self._show_orders, text='show_orders')

        self._dispatcher.register_callback_query_handler(self._edit_step_1_1, text='edit_name', state=Edit.step_1)
        self._dispatcher.register_callback_query_handler(self._edit_step_1_2, text='edit_phone_number',
                                                         state=Edit.step_1)
        self._dispatcher.register_callback_query_handler(self._edit_step_1_3, text='edit_height', state=Edit.step_1)
        self._dispatcher.register_callback_query_handler(self._edit_step_1_4, text='edit_weight', state=Edit.step_1)

        self._dispatcher.register_message_handler(self._edit_step_name, state=Edit.step_name)
        self._dispatcher.register_message_handler(self._edit_step_phone_number, state=Edit.step_phone_number)
        self._dispatcher.register_message_handler(self._edit_step_height, state=Edit.step_height)
        self._dispatcher.register_message_handler(self._edit_step_weight, state=Edit.step_weight)

        self._dispatcher.register_callback_query_handler(self._book_step_1, state=Book.step_1)
        self._dispatcher.register_callback_query_handler(self._book_step_2, state=Book.step_2)
        self._dispatcher.register_callback_query_handler(self._book_step_3, state=Book.step_3)
        self._dispatcher.register_callback_query_handler(self._book_step_4_1, text='done', state=Book.step_4)
        self._dispatcher.register_callback_query_handler(self._book_step_4_2, text='cancel', state=Book.step_4)

        self._dispatcher.register_message_handler(self._all_messages, state='*')

        self._executor._prepare_polling()
        await self._executor._startup_polling()
        self.loop.create_task(self._dispatcher.start_polling(reset_webhook=True))

    async def _bot_start(self, message: Message):
        telegram_id = message.chat.id

        check_admin = await Admin.query.where(Admin.telegram_id == str(telegram_id)).gino.first()
        if check_admin:
            await message.answer(f'Здравствуй, {check_admin.name}')
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')
            return

        check_user = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()
        if check_user:
            await message.answer(f'Здравствуйте, {check_user.name}')
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')

        if all([(not check_user), (not check_admin)]):
            await message.answer('Здравствуйте. \n'
                                 'Введите ваше ФИО, номер телефона, рост в сантиметрах и вес в килограммах.')
            example_registration = ' '.join(['Пример:', 'Иванов Иван Иванович', '+79876543210', '190', '90'])
            await self._bot.send_message(
                chat_id=telegram_id,
                text=example_registration
            )
            await Registration.step_1.set()

    async def _registration_step_1(self, message: Message, state: FSMContext):
        telegram_id = message.chat.id

        message_user = message.text.split(' ')
        if len(message_user) != 6:
            await message.answer('Введите как показано в примере!')
            return

        name_message_user = message_user[0]+' '+message_user[1]+' '+message_user[2]
        phone_number_message_user = message_user[3]
        height_message_user = message_user[4]
        weight_message_user = message_user[5]

        right_name = re.fullmatch(r'[А-ЯЁ]{1}[а-яё]{1,15}(-[А-ЯЁ]{1}[а-яё]{1,15})? [А-ЯЁ]{1}[а-яё]{1,15}(-[А-ЯЁ]{1}[а-яё]{1,15})? [А-ЯЁ]{1}[а-яё]{1,15}(-[А-ЯЁ]{1}[а-яё]{1,15})?', name_message_user)
        right_number = re.fullmatch(r'\+7\d{10}', phone_number_message_user)
        right_height = re.fullmatch(r'[1-2][0-9][0-9]', height_message_user)
        right_weight = re.fullmatch(r'[1-2]?[0-9][0-9]', weight_message_user)

        if all([(not right_weight), (not right_name), (not right_number), (not right_height)]):
            await message.answer('Введите как показано в примере!')
            return
        else:
            new_user = await User.create(
                name=name_message_user,
                phone_number=phone_number_message_user,
                height=height_message_user,
                weight=weight_message_user,
                telegram_id=str(telegram_id)
            )

            result = f"""
    Данные успешно сохранены!
    Ваше ФИО: {new_user.name}
    Ваш номер телефона: {new_user.phone_number}
    Ваш рост: {new_user.height} см
    Ваш вес: {new_user.weight} кг"""

            await self._bot.send_message(telegram_id, result)
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')
            await state.finish()

    async def _show_menu(self, message: Message):
        telegram_id = message.chat.id

        state = self._dispatcher.current_state(user=telegram_id)
        await state.reset_state()
        check_admin = await Admin.query.where(Admin.telegram_id == str(telegram_id)).gino.first()
        if check_admin:
            inline_menu = await get_kb_menu_for_admin()
            await message.answer('Здравствуйте, админстратор. Выберите интересующий Вас пункт из меню ниже:',
                                 reply_markup=inline_menu)

        check_customer = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()
        if check_customer:
            order_data = await Order.query.where(Order.telegram_id == str(telegram_id) and Order.status == 'In record').gino.all()
            if order_data:
                for order in order_data:
                    await order.delete()
            inline_menu = await get_kb_menu_for_customer()
            await message.answer('Выберите интересующий Вас пункт из меню ниже:',
                                 reply_markup=inline_menu)

        if all([(not check_customer), (not check_admin)]):
            await message.answer('Здравствуйте. \n'
                                 'Введите Ваше ФИО, номер телефона, рост в сантиметрах и вес в килограммах.')
            example_registration = ' '.join(['Пример:', 'Иванов Иван Иванович', '+79876543210', '190', '90'])
            await self._bot.send_message(
                chat_id=telegram_id,
                text=example_registration
            )
            await Registration.step_1.set()

    async def _update_db(self, callback_query: CallbackQuery):
        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        response = await new_db()
        print(response)

    async def _show_orders(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        orders_data = await Order.query.gino.all()
        text_data = ["Список заявок:"]
        k = 1
        for order in orders_data:
            if order:
                user_data = await User.query.where(User.telegram_id == order.telegram_id).gino.first()
                text_data.append(f"""
Заявка №{k}.                
ФИО: {user_data.name}.
Номер телефона: {user_data.phone_number}.
Рост и вес: {user_data.height} см и  {user_data.weight} кг.
Товар: {translation[order.ordered_subcategory]}.
Категория: {translation[order.ordered_category]}.
Длительность: {order.ordered_time}.
Статус: {translation[order.status]}.""")
                k += 1
        text = '\n'.join(text_data)

        await self._bot.send_message(
            chat_id=telegram_id,
            text=text
        )

    async def _show_links(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        inline_kb = await get_kb_out_links()
        await self._bot.send_message(telegram_id, 'Мы в соцсетях!',
                                     reply_markup=inline_kb)

    async def _book(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        inline_kb = await get_kb_category()
        await self._bot.send_message(telegram_id, 'Выберите интересующую вас категорию:',
                                     reply_markup=inline_kb)

        await Book.step_1.set()

    async def _edit(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        user_data = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()

        inline_kb = await get_kb_edit_menu()
        text = f"""
Ваши данные:
ФИО: {user_data.name}
Номер телефона: {user_data.phone_number}
Рост: {user_data.height}
Вес: {user_data.weight}
Выберите интересующий Вас пункт.
Чтобы вернуться в меню используйте команду /menu"""
        await self._bot.send_message(telegram_id, text, reply_markup=inline_kb)

        await Edit.step_1.set()

    async def _edit_step_1_1(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        await self._bot.send_message(telegram_id, 'Введите Ваше ФИО:\n'
                                                  'Пример: Иванов Иван Иванович')

        await Edit.step_name.set()

    async def _edit_step_1_2(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        await self._bot.send_message(telegram_id, 'Введите Ваш номер телефона:\n'
                                                  'Пример: +79876543210')

        await Edit.step_phone_number.set()

    async def _edit_step_1_3(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        await self._bot.send_message(telegram_id, 'Введите Ваш рост в сантиметрах:\n'
                                                  'Пример: 190')

        await Edit.step_height.set()

    async def _edit_step_1_4(self, callback_query: CallbackQuery):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        await self._bot.send_message(telegram_id, 'Введите Ваш вес в килограммах:\n'
                                                  'Пример: 80')

        await Edit.step_weight.set()

    async def _edit_step_name(self, message: Message, state: FSMContext):
        telegram_id = message.chat.id

        name_message_user = message.text

        right_name = re.fullmatch(r'[А-ЯЁ]{1}[а-яё]{1,15}(-[А-ЯЁ]{1}[а-яё]{1,15})? [А-ЯЁ]{1}[а-яё]{1,15}(-[А-ЯЁ]{1}[а-яё]{1,15})? [А-ЯЁ]{1}[а-яё]{1,15}(-[А-ЯЁ]{1}[а-яё]{1,15})?', name_message_user)
        if not right_name:
            await message.answer('Введите как показано в примере!')
            return
        else:
            user_data = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()
            await user_data.update(name=name_message_user).apply()

            await self._bot.send_message(telegram_id, f"""
Данные успешно обновлены!
    Ваше ФИО: {user_data.name}
    Ваш номер телефона: {user_data.phone_number}
    Ваш рост: {user_data.height} см
    Ваш вес: {user_data.weight} кг""")
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')

            await state.finish()

    async def _edit_step_phone_number(self, message: Message, state: FSMContext):
        telegram_id = message.chat.id

        phone_number_message_user = message.text

        right_number = re.fullmatch(r'\+7\d{10}', phone_number_message_user)
        if not right_number:
            await message.answer('Введите как показано в примере!')
            return
        else:
            user_data = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()
            await user_data.update(phone_number=str(phone_number_message_user)).apply()

            await self._bot.send_message(telegram_id, f"""
Данные успешно обновлены!
    Ваше ФИО: {user_data.name}
    Ваш номер телефона: {user_data.phone_number}
    Ваш рост: {user_data.height} см
    Ваш вес: {user_data.weight} кг""")
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')

            await state.finish()

    async def _edit_step_height(self, message: Message, state: FSMContext):
        telegram_id = message.chat.id

        height_message_user = message.text

        right_height = re.fullmatch(r'[1-2][0-9][0-9]', height_message_user)
        if not right_height:
            await message.answer('Введите как показано в примере!')
            return
        else:
            user_data = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()
            await user_data.update(height=str(height_message_user)).apply()

            await self._bot.send_message(telegram_id, f"""
Данные успешно обновлены!
    Ваше ФИО: {user_data.name}
    Ваш номер телефона: {user_data.phone_number}
    Ваш рост: {user_data.height} см
    Ваш вес: {user_data.weight} кг""")
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')

            await state.finish()

    async def _edit_step_weight(self, message: Message, state: FSMContext):
        telegram_id = message.chat.id

        weight_message_user = message.text

        right_weight = re.fullmatch(r'[1-2]?[0-9][0-9]', weight_message_user)
        if not right_weight:
            await message.answer('Введите как показано в примере!')
            return
        else:
            user_data = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()
            await user_data.update(weight=str(weight_message_user)).apply()

            await self._bot.send_message(telegram_id, f"""
Данные успешно обновлены!
    Ваше ФИО: {user_data.name}
    Ваш номер телефона: {user_data.phone_number}
    Ваш рост: {user_data.height} см
    Ваш вес: {user_data.weight} кг""")
            await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций.')

            await state.finish()

    async def _book_step_1(self, callback_query: CallbackQuery):
        call = callback_query.data
        telegram_id = callback_query.from_user.id

        user_order = await Order.create(
            telegram_id=str(telegram_id),
            ordered_category=str(call),
            status='In record'
        )

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        inline_kb = await get_kb_subcategory(str(user_order.ordered_category))
        await self._bot.send_message(telegram_id, 'Выберите интересующий вас товар:',
                                     reply_markup=inline_kb)

        await Book.step_2.set()

    async def _book_step_2(self, callback_query: CallbackQuery):
        call = callback_query.data
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        user_order = await Order.query.where(Order.telegram_id == str(telegram_id)).gino.first()

        await user_order.update(ordered_subcategory=str(call)).apply()

        inline_kb = await get_kb_time(user_order.ordered_category, user_order.ordered_subcategory)

        await self._bot.send_message(telegram_id, f'Выберите интересующее вас время:', reply_markup=inline_kb)

        await Book.step_3.set()

    async def _book_step_3(self, callback_query: CallbackQuery):
        call = callback_query.data
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        inline_kb = await get_kb_order()

        user_order = await Order.query.where(Order.telegram_id == str(telegram_id)).gino.first()
        item_data = await Item.query.where(Item.item_time_quantity == str(call) and Item.item_category == user_order.ordered_category and Item.item_subcategory == user_order.ordered_subcategory).gino.first()
        await user_order.update(ordered_time=item_data.item_time_description).apply()

        order_text = f"""
Вы выбрали товар {translation[user_order.ordered_subcategory]} из категории {translation[user_order.ordered_category]}.
Планируете забронировать на следующую длительность: {user_order.ordered_time}.
Готовы оформить эту заявку?"""

        await self._bot.send_message(telegram_id, order_text,
                                     reply_markup=inline_kb)
        await Book.step_4.set()

    async def _book_step_4_1(self, callback_query: CallbackQuery, state: FSMContext):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        right_order = await Order.query.where(Order.telegram_id == str(telegram_id)).gino.first()
        user_data = await User.query.where(User.telegram_id == str(telegram_id)).gino.first()

        await self._bot.send_message(telegram_id, 'Заявка подана. Ожидайте звонка!')
        order_text = f"""
Поступила заявка. Информация о заказчике:
ФИО: {user_data.name}
Номер телефона: {user_data.phone_number}
Рост и вес: {user_data.height} см и {user_data.weight} кг
Заказанный товар: {translation[right_order.ordered_subcategory]}
Категория товара: {translation[right_order.ordered_category]}
Длительность бронирования: {right_order.ordered_time}
Заказчик ждет вашего звонка!"""

        admin_data = await Admin.select('telegram_id').gino.all()
        admins = [x[0] for x in admin_data]
        for admin in admins:
            await self._bot.send_message(admin, order_text)

        await right_order.update(status='In progress').apply()

        await state.finish()

    async def _book_step_4_2(self, callback_query: CallbackQuery, state: FSMContext):
        telegram_id = callback_query.from_user.id

        await callback_query.answer(cache_time=60)
        await self._bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_reply_markup(reply_markup=None)

        await self._bot.send_message(telegram_id, 'Заявка сброшена.')
        await self._bot.send_message(telegram_id, 'Введите команду /menu посмотреть список доступных функций')

        wrong_order = await Order.query.where(Order.telegram_id == str(telegram_id) and Order.status == 'In record').gino.all()
        await wrong_order.delete()

        await state.finish()

    async def _all_messages(self, message: Message):
        state = self._dispatcher.current_state(user=message.chat.id)
        await state.reset_state()
        await message.answer('Команда введена неверно.')
        await self._bot.send_message(message.chat.id, 'Введите команду /menu посмотреть список доступных функций.')
