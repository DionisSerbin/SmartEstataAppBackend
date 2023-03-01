import random

import numpy as np
from xgboost import XGBRegressor
import uvicorn
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi_pagination import LimitOffsetPage, add_pagination, Page
from fastapi_pagination.ext.sqlalchemy import paginate
from geopandas.tools import geocode
import translators as ts
import translators.server as tss
from database_config import *
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, and_
from fastapi import Depends, FastAPI, Body
from fastapi.responses import JSONResponse, FileResponse
import starlette.status as status
import re
from debug_console import rest_log
import pandas as pd

Base.metadata.create_all(bind=engine)

app = FastAPI()
add_pagination(app)
user_router = InferringRouter()
admin_router = InferringRouter()
predict_router = InferringRouter()
estate_router = InferringRouter()
favourites_router = InferringRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


xgb_model = XGBRegressor()
xgb_model.load_model("xgb_model.json")


# user rest
@cbv(user_router)
class UserAPI:
    def __init__(self):
        self.MIN_LENGTH_EMAIL = 5
        self.MIN_LENGTH_NAME = 1
        self.MAX_LENGTH_EMAIL_AND_login = 50
        self.login_LENGTH = 11
        self.login_REGEX = "^\\+?[1-9][0-9]{7,14}$"
        self.EMAIL_REGEX = "^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$"

    # выбор пользователя
    @user_router.get("/api/users/{user_mail}", response_class=JSONResponse)
    async def get_user(self, user_mail: str, db: Session = Depends(get_db)):
        link = f"/api/users/{user_mail}"

        user = db.query(User).filter(User.user_mail == user_mail).first()

        if user is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.get(link=link, func=self.get_user.__name__, response=resp_json)

            return response

        rest_log.get(link=link, func=self.get_user.__name__, response=user.__dict__)

        return user

    # добавляем пользователя
    @user_router.post("/api/users", response_class=JSONResponse)
    async def create_user(self, data=Body(), db: Session = Depends(get_db)):
        link = "/api/users"


        user = User(
            user_name=data["user_name"],
            user_mail=data["user_mail"]
        )

        existed_user = db.query(User).filter(User.user_mail == user.user_mail
                                             or User.user_login == user.user_login).first()

        if existed_user is not None:
            resp_json = {"message": "Пользователь с такой почтой или с номером телефона уже существует"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.post(link=link, func=self.create_user.__name__, response=resp_json)

            return response

        if self.__wrong_validate_request(user):
            resp_json = {"message": "Неправильно введены данные"}

            response = JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=resp_json
            )

            rest_log.post(link=link, func=self.create_user.__name__, response=resp_json)

            return response

        db.add(user)
        db.commit()
        db.refresh(user)

        rest_log.post(link=link, func=self.create_user.__name__, response=user.__dict__)

        return user

    # изменение пользователя
    @user_router.put("/api/users", response_class=JSONResponse)
    async def edit_user(self, data=Body(), db: Session = Depends(get_db)):
        link = "/api/users"

        user = db.query(User).filter(User.user_id == data["user_id"]).first()

        if user is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.put(link=link, func=self.edit_user.__name__, response=resp_json)

            return response

        edited_user = User(
            user_name=data["user_name"],
            user_login=data["user_login"]
        )

        if self.__wrong_validate_request(user):
            resp_json = {"message": "Неправильно введены данные"}

            response = JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=resp_json
            )

            rest_log.put(link=link, func=self.edit_user.__name__, response=resp_json)

            return response

        user.user_name = edited_user.user_name
        user.user_mail = edited_user.user_mail
        user.user_login = edited_user.user_login

        db.commit()
        db.refresh(user)

        rest_log.put(link=link, func=self.edit_user.__name__, response=user.__dict__)

        return user

    # удаление пользователя
    @user_router.delete("/api/users/{user_mail}", response_class=JSONResponse)
    async def delete_user(self, user_mail: str, db: Session = Depends(get_db)):
        link = f"/api/users/{user_mail}"

        user = db.query(User).filter(User.user_mail == user_mail).first()

        if user is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.delete(link=link, func=self.delete_user.__name__, response=resp_json)

            return response

        db.delete(user)
        db.commit()

        rest_log.delete(link=link, func=self.delete_user.__name__, response=user.__dict__)

        return user

    def __wrong_validate_request(self, user: User):

        pattern_login = re.compile(self.login_REGEX)
        pattern_mail = re.compile(self.EMAIL_REGEX)

        return (len(user.user_login) != self.login_LENGTH
                or (len(user.user_mail) > self.MAX_LENGTH_EMAIL_AND_login or len(
                    user.user_mail) < self.MIN_LENGTH_EMAIL)
                or (len(user.user_name) > self.MAX_LENGTH_EMAIL_AND_login or len(user.user_name) < self.MIN_LENGTH_NAME)
                or not pattern_login.match(user.user_login)
                or not pattern_mail.match(user.user_mail))


# predict rest
@cbv(predict_router)
class PredictAPI:

    def __init__(self):
        self.mean_price = 3.861704259472452
        self.mean_latitude = 53.99417622805179
        self.mean_longitude = 53.494079516877704
        self.mean_region = 4355.334007490706
        self.mean_building_type = 2.37895545329201
        self.mean_level = 6.189537216596486
        self.mean_levels = 11.371798225728519
        self.mean_rooms = 1.7032101298631173
        self.mean_area = 52.781284387099916
        self.mean_kitchen_area = 10.462786904018218
        self.mean_object_type = 0.7055776250755261
        self.mean_year = 2019.3724843617772
        self.mean_month = 6.628343097815816
        self.mean_day = 16.179484811442926
        self.MILLION_VALUE = 1_000_000

    # предсказание цены
    @predict_router.get("/api/prediction", response_class=JSONResponse)
    async def get_prediction(self, data=Body()):
        link = "/api/prediction"

        predict_model = self.get_predict_model(data)

        if predict_model == None:
            resp_json = {"message": "Не правильно введен город"}
            response = JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=resp_json
            )
            rest_log.get(link=link, func=self.get_prediction.__name__, response=resp_json)
            return response

        df = pd.DataFrame(
            np.array(
                [
                    [float(predict_model.latitude)],
                    [float(predict_model.longitude)],
                    [int(predict_model.region)],
                    [int(predict_model.building_type)],
                    [int(predict_model.level)],
                    [int(predict_model.levels)],
                    [int(predict_model.rooms)],
                    [float(predict_model.area)],
                    [float(predict_model.kitchen_area)],
                    [int(predict_model.object_type)],
                    [int(predict_model.year)],
                    [int(predict_model.month)],
                    [int(predict_model.day)]
                ]
            ).transpose(),
            columns=[
                "latitude",
                "longitude",
                "region",
                "building_type",
                "level",
                "levels",
                "rooms",
                "area",
                "kitchen_area",
                "object_type",
                "year",
                "month",
                "day"
            ]
        )
        print(predict_model.longitude)
        print(predict_model.latitude)
        feature_values = df.values

        cost_predicted = xgb_model.predict(feature_values)

        response = {"prediction": f"{int(cost_predicted[0] * self.MILLION_VALUE)}"}

        rest_log.get(link=link, func=self.get_prediction.__name__, response=response)

        return response

    def get_predict_model(self, data):

        try:
            city = tss.google(data["city"], "ru", "en")
        except:
            return None

        try:
            location = geocode(city, provider="nominatim", user_agent='my_request')
        except:
            return None
        point = location.geometry.iloc[0]
        longitude = point.x
        latitude = point.y

        return PredictModel(
            day=self.get_feature(feature_string="day", data=data),
            month=self.get_feature(feature_string="month", data=data),
            year=self.get_feature(feature_string="year", data=data),
            area=self.get_feature(feature_string="area", data=data),
            kitchen_area=self.get_feature(feature_string="kitchen_area", data=data),
            levels=self.get_feature(feature_string="levels", data=data),
            level=self.get_feature(feature_string="level", data=data),
            rooms=self.get_feature(feature_string="rooms", data=data),
            building_type=self.get_feature(feature_string="building_type", data=data),
            object_type=self.get_feature(feature_string="object_type", data=data),
            region=self.mean_region,
            latitude=latitude,
            longitude=longitude
        )

    def get_feature(self, feature_string, data):
        if data[feature_string] == "":
            return self.get_mean_value(feature_string)
        else:
            return data[feature_string]

    def get_mean_value(self, feature_string):
        if feature_string == "day":
            return self.mean_day
        elif feature_string == "month":
            return self.mean_month
        elif feature_string == "year":
            return self.mean_month
        elif feature_string == "area":
            return self.mean_month
        elif feature_string == "kitchen_area":
            return self.mean_month
        elif feature_string == "levels":
            return self.mean_month
        elif feature_string == "building_type":
            return self.mean_month
        elif feature_string == "object_type":
            return self.mean_month
        return "none"


# estate rest
@cbv(estate_router)
class EstateAPI:
    def __init__(self):
        self.geo_delta = 0.4

    # выбрать всю недвижимость
    @estate_router.get("/api/estate/all", response_model=LimitOffsetPage[EstateIn])
    async def get_estates(self, db: Session = Depends(get_db)):
        link = "/api/estate/all"

        estates = self._paginate_(db.query(Estate))

        if estates is None:
            resp_json = {"message": "Недвижимость не найдена"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.get(link=link, func=self.get_estates.__name__, response=resp_json)

            return response

        rest_log.get(link=link, func=self.get_estates.__name__, response=estates.__dict__)

        return estates

    # выбрать недвижимость где
    @estate_router.get("/api/estate/where", response_model=LimitOffsetPage[EstateIn])
    async def get_estates_where(self, data=Body(), db: Session = Depends(get_db)):
        link = "/api/estates/all/where"

        est = self.get_estates_from_to(data)

        estate_from_to = self.create_condition(est, db.query(Estate))

        if estate_from_to == None:
            resp_json = {"message": "Не правильно введен город"}
            response = JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=resp_json
            )
            rest_log.get(link=link, func=self.get_estates_where.__name__, response=resp_json)
            return response

        if not estate_from_to.items:
            resp_json = {"message": "Ничего не нашлось"}
            response = JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=resp_json
            )
            rest_log.get(link=link, func=self.get_estates_where.__name__, response=resp_json)
            return response

        rest_log.get(link=link, func=self.get_estates_where.__name__, response=estate_from_to.__dict__)

        return estate_from_to

    #выбрать недвижимость пользователя
    @estate_router.get("/api/estate/user/{user_id}", response_model=LimitOffsetPage[EstateIn])
    async def get_user_estate(self, user_id: int, db: Session = Depends(get_db)):
        link = f"api/estate/user/{user_id}"

        user_estates = self._paginate_(db.query(Estate).filter(Estate.user_id == user_id))

        if user_estates is None:
            resp_json = {"message": "Недвижимость не найдена"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.get(link=link, func=self.get_user_estate.__name__, response=resp_json)

            return response

        rest_log.get(link=link, func=self.get_user_estate.__name__, response=user_estates.__dict__)

        return user_estates


    # добавить недвижимость
    @estate_router.post("/api/estate/user/", response_class=JSONResponse)
    async def create_estate(self, data=Body(), db: Session = Depends(get_db)):
        link = "/api/estates"

        try:
            city = tss.google(data["city"], "ru", "en")
        except:
            return None

        try:
            location = geocode(city, provider="nominatim", user_agent='my_request')
        except:
            return None
        point = location.geometry.iloc[0]
        longitude = point.x
        latitude = point.y

        user = db.query(User).filter(User.user_mail == data["mail"]).first()

        if user is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.post(link=link, func=self.create_estate.__name__, response=resp_json)

            return response

        estate = Estate(
            price=float(data["price"]),
            year=data["year"],
            month=data["month"],
            day=data["day"],
            time=datetime.strptime(data["time"], '%H:%M:%S').time(),
            latitude=float(latitude),
            longitude=float(longitude),
            building_type=data["building_type"],
            object_type=data["object_type"],
            levels=data["levels"],
            level=data["level"],
            rooms=data["rooms"],
            area=float(data["area"]),
            kitchen_area=float(data["kitchen_area"]),
            user_id=user.user_id
        )

        db.add(estate)
        db.commit()
        db.refresh(estate)

        rest_log.post(link=link, func=self.create_estate.__name__, response=estate.__dict__)

        return estate

    def create_condition(self, estate_from_to: EstateFomTo, db_query):

        all_filters = []
        if estate_from_to.price_from is not None:
            all_filters.append(Estate.price >= estate_from_to.price_from)
            # db_query.where(Estate.price >= estate_from_to.price_from)
        if estate_from_to.price_to is not None:
            all_filters.append(Estate.price <= estate_from_to.price_to)
            # db_query.where(Estate.price <= estate_from_to.price_to)
        if estate_from_to.area_from is not None:
            all_filters.append(Estate.area >= estate_from_to.area_from)
            # db_query.filter(Estate.area >= estate_from_to.area_from)
        if estate_from_to.area_to is not None:
            all_filters.append(Estate.area <= estate_from_to.area_to)
            # db_query.filter(Estate.area <= estate_from_to.area_to)
        if estate_from_to.kitchen_area_from is not None:
            all_filters.append(Estate.kitchen_area >= estate_from_to.kitchen_area_from)
            # db_query.filter(Estate.kitchen_area >= estate_from_to.kitchen_area_from)
        if estate_from_to.kitchen_area_to is not None:
            all_filters.append(Estate.kitchen_area <= estate_from_to.kitchen_area_to)
            # db_query.filter(Estate.kitchen_area <= estate_from_to.kitchen_area_to)
        if estate_from_to.levels_from is not None:
            all_filters.append(Estate.levels >= estate_from_to.levels_from)
            # db_query.filter(Estate.levels >= estate_from_to.levels_from)
        if estate_from_to.levels_to is not None:
            all_filters.append(Estate.levels <= estate_from_to.levels_to)
            # db_query.filter(Estate.levels <= estate_from_to.levels_to)
        if estate_from_to.level_from is not None:
            all_filters.append(Estate.level >= estate_from_to.level_from)
            # db_query.filter(Estate.level >= estate_from_to.level_from)
        if estate_from_to.level_to is not None:
            all_filters.append(Estate.level <= estate_from_to.level_to)
            # db_query.filter(Estate.level <= estate_from_to.level_to)

        if estate_from_to.rooms_from is not None:
            all_filters.append(Estate.rooms >= estate_from_to.rooms_from)
            # db_query.filter(Estate.rooms >= estate_from_to.rooms_from)
        if estate_from_to.rooms_to is not None:
            all_filters.append(Estate.rooms <= estate_from_to.rooms_to)
            # db_query.filter(Estate.rooms <= estate_from_to.rooms_to)

        if estate_from_to.building_type is not None:
            all_filters.append(Estate.building_type == estate_from_to.building_type)
            # db_query.filter(Estate.building_type == estate_from_to.building_type)

        if estate_from_to.object_type is not None:
            all_filters.append(Estate.object_type == estate_from_to.object_type)
            # db_query.filter(Estate.object_type == estate_from_to.object_type)

        if estate_from_to.latitude is not None:
            all_filters.append(Estate.latitude >= (estate_from_to.latitude - self.geo_delta))
            # db_query.where(Estate.latitude >= (estate_from_to.latitude - self.geo_delta))
            all_filters.append(Estate.latitude <= (estate_from_to.latitude + self.geo_delta))
            # db_query.where(Estate.latitude <= (estate_from_to.latitude + self.geo_delta))
        if estate_from_to.longitude is not None:
            all_filters.append(Estate.longitude >= (estate_from_to.longitude - self.geo_delta))
            # db_query.where(Estate.longitude >= (estate_from_to.longitude - self.geo_delta))
            all_filters.append(Estate.longitude <= (estate_from_to.longitude + self.geo_delta))
            # db_query.where(Estate.longitude <= (estate_from_to.longitude + self.geo_delta))
        return self._paginate_(db_query.filter(
            *all_filters
        ))

    def get_estates_from_to(self, data):
        try:
            city = tss.google(data["city"], "ru", "en")
        except:
            return None

        try:
            location = geocode(city, provider="nominatim", user_agent='my_request')
        except:
            return None
        point = location.geometry.iloc[0]
        longitude = point.x
        latitude = point.y

        return EstateFomTo(
            area_from=float(self.get_feature(feature_string="area_from", data=data))
            if self.get_feature(feature_string="area_from", data=data) is not None else None,

            area_to=float(self.get_feature(feature_string="area_to", data=data))
            if self.get_feature(feature_string="area_to", data=data) is not None else None,

            kitchen_area_from=float(self.get_feature(feature_string="kitchen_area_from", data=data))
            if self.get_feature(feature_string="kitchen_area_from", data=data) is not None else None,

            kitchen_area_to=float(self.get_feature(feature_string="kitchen_area_to", data=data))
            if self.get_feature(feature_string="kitchen_area_to", data=data) is not None else None,

            levels_from=self.get_feature(feature_string="levels_from", data=data),
            levels_to=self.get_feature(feature_string="levels_to", data=data),
            level_from=self.get_feature(feature_string="level_from", data=data),
            level_to=self.get_feature(feature_string="level_to", data=data),
            rooms_from=self.get_feature(feature_string="rooms_from", data=data),
            rooms_to=self.get_feature(feature_string="rooms_to", data=data),

            price_from=float(self.get_feature(feature_string="price_from", data=data))
            if self.get_feature(feature_string="price_from", data=data) is not None else None,

            price_to=float(self.get_feature(feature_string="price_to", data=data))
            if self.get_feature(feature_string="price_to", data=data) is not None else None,

            building_type=self.get_feature(feature_string="building_type", data=data),
            object_type=self.get_feature(feature_string="object_type", data=data),
            latitude=float(latitude),
            longitude=float(longitude)
        )

    def get_feature(self, feature_string, data):
        if data[feature_string] == "":
            return None
        else:
            return data[feature_string]

    def _paginate_(self, db_query):
        return paginate(db_query
                        .order_by(asc(Estate.year))
                        .order_by(asc(Estate.month))
                        .order_by(asc(Estate.day))
                        .order_by(asc(Estate.time))
                        )


#favourites rest
@cbv(favourites_router)
class FavouritesAPI:

    # Добавить в закладки
    @favourites_router.post("/api/favourites", response_class=JSONResponse)
    async def create_favourite(self, user_mail: str, estate_id: int, db: Session = Depends(get_db)):
        link = "/api/favourites"

        user_favourite = db.query(User).filter(User.user_mail == user_mail).first()

        if user_favourite is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.post(link=link, func=self.create_favourite.__name__, response=resp_json)

            return response

        favourite = Favourites(
            user_id=user_favourite.user_id,
            estate_id=estate_id
        )

        db.add(favourite)
        db.commit()
        db.refresh(favourite)

        rest_log.post(link=link, func=self.create_favourite.__name__, response=favourite.__dict__)

        return favourite

    # Удалить закладку
    @favourites_router.delete("/api/favourites", response_class=JSONResponse)
    async def delete_favourite(self, user_mail: str, estate_id: int, db: Session = Depends(get_db)):
        link = "/api/favourites"

        user_favourite = db.query(User).filter(User.user_mail == user_mail).first()

        if user_favourite is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.post(link=link, func=self.delete_favourite.__name__, response=resp_json)

            return response

        favourite = db.query(Favourites).filter(and_(
            Favourites.user_id == user_favourite.user_id,
            Favourites.estate_id == estate_id
        )).first()
        db.delete(favourite)
        db.commit()

        rest_log.delete(link=link, func=self.delete_favourite.__name__, response=favourite.__dict__)

        return favourite

    # Выбрать из закладок
    @favourites_router.get("/api/favourites/{user_mail}", response_class=JSONResponse)
    async def get_favourites_estate(self, user_mail: str, db: Session = Depends(get_db)):
        link = f"/api/favourites/{user_mail}"

        user_favourite = db.query(User).filter(User.user_mail == user_mail).first()

        if user_favourite is None:
            resp_json = {"message": "Пользователь не найден"}

            response = JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=resp_json
            )

            rest_log.get(link=link, func=self.get_favourites_estate.__name__, response=resp_json)

            return response

        favourites = db.query(Favourites).filter(Favourites.user_id == user_favourite.user_id)

        favourite_estates = []
        for favourite in favourites:
            estate_id = favourite.estate_id
            favourite_estate = db.query(Estate).filter(Estate.estate_id == estate_id).first()
            favourite_estates.append(favourite_estate)

        rest_log.get(link=link, func=self.get_favourites_estate.__name__, response=favourite_estates)

        return favourite_estates


app.include_router(
    favourites_router,
    tags=["FavouritesIn"]
)
app.include_router(estate_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(predict_router)
add_pagination(app)

if __name__ == "__main__":
    uvicorn.run(app, host="192.168.3.33", port=8080)
