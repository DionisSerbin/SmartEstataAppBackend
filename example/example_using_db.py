from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI

# SQlite имплементирование
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# СУБД имплементирование
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"


# создание движка
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

Base = declarative_base()


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer, )


# создаем таблицы
Base.metadata.create_all(bind=engine)

# приложение, которое ничего не делает
app = FastAPI()

SessionLocal = sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()

# после добавления или обновления объекта, если мы хотим использовать этот объект,
# обращаться к его атрибутами, то желательно, а иногда может быть необходимо,
# использовать метод refresh(), который обновляет состояние объекта
tom = Person(name="Tom", age=38)
alice = Person(name="Alice", age=33)
kate = Person(name="Kate", age=28)
db.add_all([tom, alice, kate])
db.commit()
db.refresh(tom)

# SELECT * FROM Person
people = db.query(Person).all()
for p in people:
    print(f"{p.id}.{p.name} ({p.age})")

print("-" * 5)

# select by id
first_person = db.get(Person, 1)
print(f"{first_person.name} - {first_person.age}")

print("-" * 5)

# select where
people_filter = db.query(Person).filter(Person.age > 35).all()
for p in people_filter:
    print(f"{p.id}.{p.name} ({p.age})")

print("-" * 5)
# select where and choose first
first = db.query(Person).filter(Person.id == 1).first()
print(f"{first.name} ({first.age})")

print("-" * 5)

# update
tom = db.query(Person).filter(Person.id == 1).first()
print(f"{tom.id}.{tom.name} ({tom.age})")

tom.name = "Tomas"
tom.age = 22

db.commit()

tomas = db.query(Person).filter(Person.id == 1).first()
print(f"{tomas.id}.{tomas.name} ({tomas.age})")

print("-" * 5)

# удаление
bob = db.query(Person).filter(Person.id == 2).first()
db.delete(bob)  # удаляем объект
db.commit()  # сохраняем изменения
