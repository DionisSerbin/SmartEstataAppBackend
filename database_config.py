from datetime import date, datetime, timedelta, time
from typing import Optional

from fastapi_pagination.bases import AbstractParams
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, Time
from pydantic import BaseModel

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:1111@localhost:3306/dipl"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()


class User(Base):
    __tablename__ = "User"

    user_id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_mail = Column(String(100), unique=True, nullable=False)
    user_login = Column(String(30), unique=True, nullable=True)
    user_name = Column(String(30), nullable=True)


class Estate(Base):
    __tablename__ = "Estate"

    estate_id = Column(Integer, primary_key=True, index=True, nullable=False)
    price = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    time = Column(Time(timezone=True))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(Integer, nullable=True)
    building_type = Column(Integer, nullable=True)
    level = Column(Integer, nullable=True)
    levels = Column(Integer, nullable=True)
    rooms = Column(Integer, nullable=True)
    area = Column(Float, nullable=True)
    kitchen_area = Column(Float, nullable=True)
    object_type = Column(Integer, nullable=True)
    address = Column(String(200), nullable=True)
    region_name = Column(String(100), nullable=True)
    user_id = Column(
        Integer,
        ForeignKey('User.user_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )


class EstateIn(BaseModel):
    estate_id: int
    price: float
    year: int
    month: int
    day: int
    time: time
    latitude: float
    longitude: float
    region: Optional[int] = ...
    building_type: int
    level: int
    levels: int
    rooms: int
    area: float
    kitchen_area: float
    object_type: int
    address: Optional[str] = ...
    region_name: Optional[int] = ...
    user_id: Optional[int] = ...

    class Config:
        orm_mode = True


class Favourites(Base):
    __tablename__ = "Favourites"

    user_id = Column(
        Integer,
        ForeignKey('User.user_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        primary_key=True
    )

    estate_id = Column(
        Integer,
        ForeignKey('Estate.estate_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        primary_key=True
    )


class PredictModel:
    def __init__(self, year, month, day, latitude, longitude,
                 region, building_type, level, levels, rooms, area,
                 kitchen_area, object_type):
        self.year = year
        self.month = month
        self.day = day
        self.latitude = latitude
        self.longitude = longitude
        self.region = region
        self.building_type = building_type
        self.level = level
        self.levels = levels
        self.rooms = rooms
        self.area = area
        self.kitchen_area = kitchen_area
        self.object_type = object_type


class EstateFomTo:
    def __init__(self, latitude, longitude, building_type, object_type,
                 price_from, price_to, level_from, level_to, levels_from, levels_to,
                 rooms_from, rooms_to, area_from, area_to, kitchen_area_from,
                 kitchen_area_to):
        self.latitude = latitude
        self.longitude = longitude
        self.building_type = building_type
        self.level_from = level_from
        self.level_to = level_to
        self.levels_from = levels_from
        self.levels_to = levels_to
        self.rooms_from = rooms_from
        self.rooms_to = rooms_to
        self.area_from = area_from
        self.area_to = area_to
        self.kitchen_area_from = kitchen_area_from
        self.kitchen_area_to = kitchen_area_to
        self.price_from = price_from
        self.price_to = price_to
        self.object_type = object_type


SessionLocal = sessionmaker(autoflush=False, bind=engine)
