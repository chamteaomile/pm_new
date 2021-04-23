import requests

from database import Item, Order, User

response = requests.get('http://194.67.110.125:8080/prices')
if response == 200:
    future_db = response.json()
    counter = 0
    for item in future_db:
        item_time_quantity = future_db[counter]['timeEntity']['time']
        item_time_description = future_db[counter]['timeEntity']['name']
        item_price = future_db[counter]['value']
        item_category = future_db[counter]['categoryEntity']['name']
        item_subcategory = future_db[counter]['subCategoryEntity']['name']
        item = future_db[counter]['subCategoryEntity']['categories']['name']
        new_item =
        counter += 0

