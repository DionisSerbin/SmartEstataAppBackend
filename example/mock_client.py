import uuid
import json
import requests

link = "http://127.0.0.1:8000/api"


class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.id = str(uuid.uuid4())


def my_print(response):
    print("-" * 10)
    print(response.text)


response = requests.get(f"{link}/users")

my_print(response)

my_person = {"name": "Denis", "age": 21}

response = requests.post(f"{link}/users/", json=my_person)

person_id = response.json()["id"]

response = requests.get(f"{link}/users")

my_print(response)

my_person = {"name": "Denis", "age": 19, "id": person_id}

response = requests.put(f"{link}/users", json=my_person)

response = requests.get(f"{link}/users")

my_print(response)

response = requests.delete(f"{link}/users/{person_id}")

my_print(response)
