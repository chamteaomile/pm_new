import requests

from database import Item


async def update_db(url):
    response = requests.get(url)
    if response == 200:
        future_db = response.json()
        counter = 0
        for thing in future_db:
            item_name = future_db[counter]['subCategoryEntity']['categories'][0]['name']
            item_category = future_db[counter]['categoryEntity']['name']
            item_subcategory = future_db[counter]['subCategoryEntity']['name']
            item_time_quantity = str(future_db[counter]['timeEntity']['time'])
            item_time_description = future_db[counter]['timeEntity']['name']
            item_price = str(future_db[counter]['value'])
            new_item = await Item.create(
                item_name=item_name,
                item_category=item_category,
                item_subcategory=item_subcategory,
                item_time_quantity=item_time_quantity,
                item_time_description=item_time_description,
                item_price=item_price
            )
            counter += 0

await update_db('http://194.67.110.125:8080/prices')
