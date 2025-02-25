import jwt.exceptions
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from pydantic import BaseModel
from typing import Literal
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import JWTException

# JWT
SECRET_KEY = "acbdsigmasigmaboy"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Baza
engine = create_engine('sqlite:///zad_python.db')
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    min_duration: int | None = 30    # jeśli nie zostanie podane, default to 30
    max_duration: int | None = 480   # ^^, default to 480

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

class Token(BaseModel):
    token: str
    type: str

class TokenData(BaseModel):
    username: str | None = None


# Zabezpieczenia
context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify(password, hash):
    return context.verify(password, hash)

def hash(password):
    return context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Połączenie z bazą
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def get_curr_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db())):
    credentials_exception = HTTPException(status_code=400, detail="Provided data is wrong")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
        data = TokenData(username=username)
    except JWTException:
        raise credentials_exception
    
    user = get_user_by_username(db, username=data.username)
    if not user:
        raise credentials_exception
    
    return user

# ------

app = FastAPI()

@app.post("/register", response_model=ReturnUser)
async def register(user: CreateUser, db: Session = Depends(db())):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="This user already exists")
    
    new_user = User(username=user.username, password=hash(user.password), admin=user.admin)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
async def login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db())):
    user = get_user_by_username(db, data.username)
    if not user or not verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Login failed")
    
    access_token = create_access_token(data={"sub": user.username})
