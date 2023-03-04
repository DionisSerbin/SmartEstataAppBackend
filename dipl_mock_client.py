import uuid
import json
import requests
from starlette.responses import JSONResponse

import database_config


def my_print(response):
    print("-" * 10)
    print(response.text)


def test_user(link):
    # post
    my_user = {"user_mail": "reag@gmail.com", "user_phone": "89269098365", "user_name": "Demis"}
    response = requests.post(link, json=my_user)
    my_print(response)

    # get
    response = requests.get(f"{link}/6")
    my_print(response)

    # put
    ma_user = {"user_mail": "reag@gmail.com", "user_phone": "89269098365", "user_name": "Dis", "user_id": 6}
    response = requests.put(link, json=ma_user)
    my_print(response)

    # delete
    response = requests.delete(f"{link}/6")
    my_print(response)


def test_predict(link):
    my_predict = {'city': 'Москва', 'houseType': 3, 'kitchenAreaFrom': '', 'kitchenAreaTo': '', 'levelFrom': '',
                  'levelTo': '', 'levelsFrom': '', 'levelsTo': '', 'numberOfRoomsFrom': '', 'numberOfRoomsTo': '',
                  'objectType': -1, 'totalAreaFrom': '', 'totalAreaTo': ''}
    response = requests.post(link, json=my_predict)
    my_print(response)


def test_estates(link):
    response = requests.get(f"{link}/all?limit=5&offset=20")
    my_print(response)
    ma_estate = {
        "area_from": 56.5,
        "area_to": 80.5,
        "kitchen_area_from": 5,
        "kitchen_area_to": 30,
        "levels_from": 10,
        "levels_to": 35,
        "level_from": 14,
        "level_to": 35,
        "rooms_from": 2,
        "rooms_to": 9,
        "price_from": 1.0,
        "price_to": 15.0,
        "building_type": 2,
        "object_type": 1,
        "city": "Москва"
    }
    response = requests.get(f"{link}/where?limit=5&offset=20", json=ma_estate)
    my_print(response)

    ma_estate = {
        "area": 56.5,
        "kitchen_area": 5,
        "levels": 35,
        "level": 14,
        "rooms": 2,
        "price": 1.0,
        "building_type": 2,
        "object_type": 1,
        "city": "Москва",
        "year": 2022,
        "month": 2,
        "day": 25,
        "time": "13:40:25",
        "mail": "re@gmail.com"
    }
    response = requests.post(f"{link}/user", json=ma_estate)
    print(response)

    response = requests.get(f"{link}/user/1?limit=5&offset=0")
    print(response.text)


def test_favourite(link):
    # response = requests.post(f"{link}?user_mail=re@gmail.com&estate_id=1")
    # my_print(response)

    response = requests.get(f"{link}/re@gmail.com")
    my_print(response)

    response = requests.delete(f"{link}?user_mail=re@gmail.com&estate_id=1")
    my_print(response)


if __name__ == '__main__':
    # test_user(link="http://192.168.3.33:8080/api/users")
    test_predict(link="http://192.168.3.33:8080/api/prediction")
    # test_estates(link="http://192.168.3.33:8080/api/estate")
    # test_favourite(link="http://192.168.3.33:8080/api/favourites")
    # test_user_string()
