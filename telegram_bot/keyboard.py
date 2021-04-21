from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import Item


async def get_kb_menu_for_customer():
    inline_btn_show_book = InlineKeyboardButton('Бронирование', callback_data='book')
    inline_btn_show_links = InlineKeyboardButton('Ссылки на другие соцсети', callback_data='links')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_show_book, inline_btn_show_links)
    return inline_kb_menu


async def get_kb_menu_for_admin():
    inline_btn_show_book = InlineKeyboardButton('Бронирование', callback_data='book')
    inline_btn_show_links = InlineKeyboardButton('Соцсети', callback_data='links')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_show_book, inline_btn_show_links)
    return inline_kb_menu


async def get_kb_items_to_book():
    inline_kb = InlineKeyboardMarkup(row_width=1)
    all_items = await Item.query.gino.all()
    for item in all_items:
        inline_kb.add(InlineKeyboardButton(f'{item.name}', callback_data=f'it:{item.name}'))
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
