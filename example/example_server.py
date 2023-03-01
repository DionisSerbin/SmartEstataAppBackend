from datetime import datetime

from fastapi import FastAPI, Path, Query, Body, Header, Cookie
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse, FileResponse, Response, RedirectResponse, PlainTextResponse
from typing import List

import starlette.status as status


from debug_console import *

app = FastAPI()


# для асинхронной работы прример:
# @app.post("/dummypath")
# async def get_body(request: Request):
#     return await request.json()

# корень
@app.get("/", response_class=JSONResponse)
def root():
    response = {"message": "Hello METANIT.COM"}
    rest_log.get(link="/", func=root.__name__, response=response)
    return response


# разные пути
@app.get("/about", response_class=JSONResponse)
def about():
    return {"message": "О сайте"}


# работа с файлами
@app.get("/file", response_class=FileResponse)
def file():
    return "filepath..."


# важно учитывать очередность определения шаблонов путей
# @app.get("/users/admin", response_class=JSONResponse)
@app.get("/users/admin/admin", response_class=JSONResponse)
def admin():
    response = {"message": "Hello admin"}
    rest_log.get(link=f"/users/admin", func=admin.__name__, response=response)
    return response


# работа с запросами типа: /users?name=Tom&age=76
@app.get("/users", response_class=JSONResponse)
def get_model(name: str = Query(min_length=2, max_length=45),
              age: int = Query(default=None, gt=0, le=120)):

    response = {"user_name": name, "user_age": age}
    rest_log.get(link=f"/users?name={name}&age={age}",
                 func=users.__name__, response=response)
    if age is None:
        return {"user_name": name}
    return response


# схожий вариант, но просто с передачей переменной
@app.get("/users/{name}&{age}", response_class=JSONResponse)
def users(name: str = Path(min_length=2, max_length=45), age: int = Path(gt=0, le=120)):
    response = {"user_name": name, "user_age": age}
    rest_log.get(link=f"/users/{name}&{age}", func=users.__name__, response=response)
    return response


# работа с regex
@app.get("/users/phone/{phone}", response_class=JSONResponse)
def users(phone: str = Path(regex="^\d{11}$")):
    response = {"phone": phone}
    rest_log.get(link=f"/users/{phone}", func=users.__name__, response=response)
    return response


# передача одного параметра
@app.get("/users/id/{id}", response_class=JSONResponse)
def users(id: int):
    response = {"user_id": id}
    rest_log.get(link=f"/users/id/{id}", func=users.__name__, response=response)
    return response


# передача двух параметров
@app.get("/nameage/{name}/{age}", response_class=JSONResponse)
def users(name: str, age: int):
    response = {"user_name": name, "user_age": age}
    rest_log.get(link=f"/users/{name}/{age}", func=users.__name__, response=response)
    return response


# передача списка
@app.get("/people")
def get_people(people: List[str] = Query()):
    response = {"people": people}
    rest_log.get(link="/people", func=get_people.__name__, response=response)
    return response


# комбинирование пути и строки запроса: /combine/Tom?age=38
@app.get("/combine/{name}")
def combine_path_query(name: str = Path(min_length=3, max_length=20),
                       age: int = Query(ge=18, lt=111)):
    response = {"name": name, "age": age}
    rest_log.get(link=f"/combine/{name}?age={age}",
                 func=combine_path_query.__name__, response=response)
    return response


# получение кастомного кода
@app.get("/notfound", status_code=status.HTTP_404_NOT_FOUND)
def notfound():
    response = {"message": "Resource Not Found"}
    rest_log.get(link="/notfound", func=notfound.__name__, response=response)
    return response


# поулчение кастомного кода при условии
@app.get("/notfound/{id}", status_code=status.HTTP_200_OK)
def notfound_option(response: Response, id: int = Path()):
    if id < 1:
        resp_str = {"message": "Incorrect Data"}
        rest_log.get(link=f"/notfound/{id}",
                     func=notfound_option.__name__, response=resp_str)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return resp_str

    resp_str = {"message": f"Id = {id}"}
    rest_log.get(link=f"/notfound/{id}",
                 func=notfound_option.__name__, response=resp_str)
    return resp_str


# переадресация
@app.get("/old/{digit}")
def old(digit: int):
    if digit == 1:
        return RedirectResponse("/new")
    else:
        return RedirectResponse("https://metanit.com/python/fastapi")


@app.get("/new")
def new():
    return PlainTextResponse("Новая страница")


# получение json данных на сервер
@app.post("/hello")
# def hello(name = Body(embed=True)):
def hello(data=Body()):
    name = data["name"]
    age = data["age"]
    response = {"message": f"{name}, ваш возраст - {age}"}
    rest_log.post(link="/hello", func=hello.__name__, response=response)
    return response


# получение данных с валидацией
@app.post("/hello")
def hello(name: str = Body(embed=True, min_length=3, max_length=20),
          age: int = Body(embed=True, ge=18, lt=111)):
    response = {"message": f"{name}, ваш возраст - {age}"}
    rest_log.post(link="/hello", func=hello.__name__, response=response)
    return response


# получение данных как класса
class Person(BaseModel):
    name: str = Field(default="Undefined", min_length=3, max_length=20)
    age: int = Field(default=None, ge=18, lt=111)
    languages: list = ["Eng", "Rus"]


@app.post("/person")
def person_func(person: Person):
    if person.age == None:
        return {"message": f"Привет, {person.name}"}
    else:
        return {"message": f"Name: {person.name}. Languages: {person.languages}"}


# получение списка класса
@app.post("/hello")
def hello(people: List[Person]):
    return {"message": people}


class Company(BaseModel):
    name: str


class Person2(BaseModel):
    name: str
    company: Company


# вложенные модели
@app.post("/hello")
def hello(person: Person2):
    return {"message": f"{person.name} ({person.company.name})"}


# отправка заголовков
@app.get("/headers")
def get_headers(response: Response):
    response.headers["Secret-Code"] = "123459"
    return {"message": "Hello METANIT.COM"}


# либо
@app.get("/headersOther")
def get_headers(response: Response):
    data = "Hello METANIT.COM"
    return Response(content=data, media_type="text/plain", headers={"Secret-Code": "123459"})


#получение заголовков
@app.get("/headerGet")
def root(user_agent: str = Header(default=None)):
    return {"User-Agent": user_agent}

#куки положить
@app.get("/cookie")
def cookie(response: Response):
    now = datetime.now()    # получаем текущую дату и время
    response.set_cookie(key="last_visit", value=now)
    return  {"message": "куки установлены"}

#получить куки
@app.get("/cookieGet")
def cookie(last_visit = Cookie(default=None)):
    return  {"last visit": last_visit}