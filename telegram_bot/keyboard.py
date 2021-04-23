from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import Item, Order, User


async def get_kb_menu_for_customer():
    inline_btn_show_book = InlineKeyboardButton('Бронирование', callback_data='book')
    inline_btn_show_links = InlineKeyboardButton('Ссылки на другие соцсети', callback_data='links')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_show_book, inline_btn_show_links)
    return inline_kb_menu


async def get_kb_menu_for_admin():
    inline_btn_show_orders = InlineKeyboardButton('Посмотреть заявки', callback_data='show_orders')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_show_orders)
    return inline_kb_menu


async def get_kb_orders_menu():
    inline_kb = InlineKeyboardMarkup(row_width=1)
    all_orders = await Order.query.gino.all()
    for order in all_orders:
        user_data = await User.query.where(User.telegram_id == order.telegram_id).gino.first()
        user_name = user_data.name.split(' ')
        user_nick = user_name[0]
        inline_kb.add(InlineKeyboardButton(f'{user_nick}: {order.ordered_item}', callback_data=f'{order.id}'))
    return inline_kb


async def get_kb_status_menu():
    inline_btn_in_progress = InlineKeyboardButton('В процессе', callback_data='in_progress')
    inline_btn_done = InlineKeyboardButton('Сделано', callback_data='done')
    inline_btn_canceled = InlineKeyboardButton('Отменено', callback_data='canceled')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_in_progress, inline_btn_done, inline_btn_canceled)
    return inline_kb_menu


async def get_kb_items_to_book():
    inline_kb = InlineKeyboardMarkup(row_width=1)
    all_items = await Item.query.gino.all()
    for item in all_items:
        inline_kb.add(InlineKeyboardButton(f'{item.name}', callback_data=f'{item.data}'))
    return inline_kb


async def get_kb_out_links():
    inline_btn_vk = InlineKeyboardButton(text='Вконтакте', url='https://vk.com/mokat_prokat')
    inline_btn_inst = InlineKeyboardButton(text='Инстаграмм', url='https://www.instagram.com/prokatmokat/')
    inline_btn_site = InlineKeyboardButton(text='Наш сайт', url='https://mokat-prokat.ru/')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_vk, inline_btn_inst, inline_btn_site)
    return inline_kb_menu


async def get_kb_order():
    inline_btn_ok = InlineKeyboardButton('Оформить', callback_data='done')
    inline_btn_not_ok = InlineKeyboardButton('Отмена', callback_data='cancel')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_ok, inline_btn_not_ok)
    return inline_kb_menu
