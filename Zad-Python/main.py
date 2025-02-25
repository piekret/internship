from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

# Baza
engine = create_engine('sqlite:///zad_python.db')
Base = declarative_base()
Session = sessionmaker()
session = Session(bind=engine)


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    location = Column(String)
    availability = Column(String)
    min_duration = Column(Integer, default=30)
    max_duration = Column(Integer, default=480)
    reservations = relationship("Reservation", back_populates="resource")



class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    admin = Column(Integer, default=0)
    reservations = relationship("Reservation", back_populates="user")


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    users = relationship("User", back_populates="reservations")
    resources = relationship("Resource", back_populates="reservations")
    

Base.metadata.create_all(bind=engine)


# Schematy do walidacji
class CreateResource(BaseModel):
    name: str
    resource_type: str
    location: str
    availability: str
    min_duration: Optional[int] = 30    # jeśli nie zostanie podane, default to 30
    max_duration: Optional[int] = 480   # ^^, default to 480

class ReturnResource(BaseModel):
    id: int
    name: str
    resource_type: str
    location: str
    availability: str
    min_duration: int
    max_duration: int
    class Config:
        orm_mode = True     # pozwala modelowi bezpośrednie pracowanie z obiektami ORM


class CreateUser(BaseModel):
    username: str
    password: str
    admin: Literal[0, 1]    # "admin" może być albo 0 albo 1

class ReturnUser(BaseModel):
    id: int
    username: str
    admin: int
    class Config:
        orm_mode = True

class CreateReservation(BaseModel):
    resource_id: int
    start_datetime: datetime
    end_datetime: datetime

class ReturnReservation(BaseModel):
    id: int
    user_id: int
    resource_id: int
    start_date: datetime
    end_date: datetime
    class Config:
        orm_mode = True

