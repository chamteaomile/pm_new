from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import Item, Order, User


translation = {
    "SCOOTER": "самокат",
    "ROLLER": "ролики",
    "WINTER_SKATES": "коньки",
    "LONGBOARD": "лонгборд",
    "CYCLECAR": "веломобиль",
    "BIKE": "велосипед",
    "TANDEM_BIKE": "двуместный велосипед",
    "KIDS_CYCLECAR": "детский веломобиль",
    "KIDS_TRICYCLE_SCOOTER": "детский трехколесный самокат",
    "KIDS_BIKE_CHAIR": "детское велосипедное кресло",
    "FOR_KIDS": "для детей",
    "ELECTRIC_SINGLE_KIDS_CAR": "детский одноместный электромобиль",
    "KIDS_ROLLER": "детские ролики",
    "ADULT_MICRO_SCOOTER": "сегвей для взрослого",
    "ADULT_ROLLER": "ролики для взрослого",
    "ADULT_SUSP_YEDOO_SCOOTER": "самокат yeed для взрослого",
    "TEEN_OXELO_SCOOTER": "самокат oxelo для подростка",
    "TEEN_CITY_BIKE": "городской велосипед для подростка",
    "SPORT_EQUIPMENT": "спортивный инвентарь",
    "ELECTRICAL_EQUIP": "электрический инвентарь",
    "SPEED_BIKE": "скоростной велосипед",
    "CITY_BIKE": "городской велосипед",
    "MALE_WINTER_SKATES": "мужские коньки",
    "FEMALE_WINTER_SKATES": "женские коньки",
    "NORMAL": "нормальные",
    "SINGLE_CYCLECAR": "одноместный веломобиль",
    "DOUBLE_CYCLECAR": "двуместный веломобиль",
    "TRIPLE_CYCLECAR": "трехместный веломобиль",
    "FIVE_SEATER_CYCLECAR": "пятиместный веломобиль",
    "ELECTRIC_GEROSCHOOTER": "гироскутер",
    "ELECTRIC_SEGWAY_MINI_LITE": "сигвей мини лайт",
    "ELECTRIC_SEGWAY_MINI_PRO": "сигвей мини про",
    "BALL": "мяч",
    "ELECTRIC_SCOOTER": "электросамокат",
    "In record": "заявка заполняется",
    "In progress": "заявка в обработке",
    "Accepted": "заявка принята"
}


async def get_kb_menu_for_customer():
    inline_btn_edit_user_data = InlineKeyboardButton('Изменить свои данные', callback_data='edit')
    inline_btn_show_book = InlineKeyboardButton('Бронирование', callback_data='book')
    inline_btn_show_links = InlineKeyboardButton('Ссылки на другие соцсети', callback_data='links')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_edit_user_data, inline_btn_show_book, inline_btn_show_links)
    return inline_kb_menu


async def get_kb_menu_for_admin():
    inline_btn_show_orders = InlineKeyboardButton('Посмотреть заявки', callback_data='show_orders')
    inline_btn_update_db = InlineKeyboardButton('Обновить базу данных', callback_data='update_db')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_show_orders, inline_btn_update_db)
    return inline_kb_menu


async def get_kb_edit_menu():
    inline_btn_edit_name = InlineKeyboardButton('Изменить ФИО', callback_data='edit_name')
    inline_btn_edit_phone_number = InlineKeyboardButton('Изменить номер телефона', callback_data='edit_phone_number')
    inline_btn_edit_height = InlineKeyboardButton('Изменить рост', callback_data='edit_height')
    inline_btn_edit_weight = InlineKeyboardButton('Изменить вес', callback_data='edit_weight')
    inline_kb_menu = InlineKeyboardMarkup(row_width=1)
    inline_kb_menu.add(inline_btn_edit_name, inline_btn_edit_phone_number, inline_btn_edit_height,
                       inline_btn_edit_weight)
    return inline_kb_menu


async def get_kb_category():
    inline_kb = InlineKeyboardMarkup(row_width=1)
    all_categories = await Item.select('item_category').gino.all()
    unique_categories = []
    for a in all_categories:
        if a in unique_categories:
            continue
        else:
            unique_categories.append(a)
    result_categories = [x[0] for x in unique_categories]
    for category in result_categories:
        inline_kb.add(InlineKeyboardButton(f'{translation[category]}', callback_data=f'{category}'))
    return inline_kb


async def get_kb_subcategory(category):
    inline_kb = InlineKeyboardMarkup(row_width=1)
    all_subcategories = await Item.select('item_subcategory').where(Item.item_category == category).gino.all()
    unique_subcategories = []
    for a in all_subcategories:
        if a in unique_subcategories:
            continue
        else:
            unique_subcategories.append(a)
    result_subcategories = [x[0] for x in unique_subcategories]
    for subcategory in result_subcategories:
        inline_kb.add(InlineKeyboardButton(f'{translation[subcategory]}', callback_data=f'{subcategory}'))
    return inline_kb


async def get_kb_time(category, subcategory):
    inline_kb = InlineKeyboardMarkup(row_width=1)
    all_time_description = await Item.select('item_time_description').where(Item.item_category == category and Item.item_subcategory == subcategory).gino.all()
    all_time_quantity = await Item.select('item_time_quantity').where(Item.item_category == category and Item.item_subcategory == subcategory).gino.all()
    unique_time_description = []
    unique_time_quantity = []
    for a in all_time_description:
        if a in unique_time_description:
            continue
        else:
            unique_time_description.append(a)
    for b in all_time_quantity:
        if b in unique_time_quantity:
            continue
        else:
            unique_time_quantity.append(b)
    result_time_description = [x[0] for x in unique_time_description]
    result_time_quantity = [x[0] for x in unique_time_quantity]
    i = 0
    while i < len(result_time_quantity):
        inline_kb.add(InlineKeyboardButton(f'{result_time_description[i]}', callback_data=f'{result_time_quantity[i]}'))
        i += 1
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
