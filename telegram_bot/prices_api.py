import requests
import asyncio

from database import Item


async def new_db():
    response = requests.get('http://194.67.110.125:8080/prices')
    future_db = response.json()
    counter_first = 0
    for a in future_db:
        item_time_quantity = str(future_db[counter_first]['timeEntity']['time'])
        item_time_description = future_db[counter_first]['timeEntity']['name']
        item_price = str(future_db[counter_first]['value'])
        item_category = future_db[counter_first]['categoryEntity']['name']
        item_subcategory = future_db[counter_first]['subCategoryEntity']['name']
        await Item.create(
            item_category=item_category,
            item_subcategory=item_subcategory,
            item_time_quantity=item_time_quantity,
            item_time_description=item_time_description,
            item_price=item_price
        )
        counter_first += 1
    return response
