from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from pydantic import BaseModel
from typing import Literal
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import JWTException
import smtplib

# JWT
SECRET_KEY = "acbdsigmasigmaboy"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# SMTP
SENDER_EMAIL = "dla_projektu@adresik.net"
SENDER_PASSWORD = "!dlaProjektu"

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
    email = Column(String)
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
    email: str
    admin: Literal[0, 1]    # "admin" może być albo 0 albo 1

class ReturnUser(BaseModel):
    id: int
    username: str
    email: str
    admin: int
    class Config:
        orm_mode = True

class CreateReservation(BaseModel):
    resource_id: int
    start_date: datetime
    end_date: datetime

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


# Połączenie z bazą + funkcje pomocnicze
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def get_curr_user(token: str = Depends(oauth2_scheme), db: Session = Depends(db)):
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

def conflit(db: Session, resource_id: int, start_date: datetime, end_date: datetime,  reservation_id: int | None = None):
    result = db.query(Reservation).filter(
        Reservation.resource_id == resource_id,
        Reservation.start_date == start_date,
        Reservation.end_date == end_date
    )

    if reservation_id:
        result = result.filter(Reservation.id != reservation_id)

    return db.query(result.exists()).scalar()

def send_email(receiver: str, msg: str):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(SENDER_EMAIL, SENDER_PASSWORD)
    s.send_message(SENDER_EMAIL, receiver, msg)
    s.quit()


# ------

app = FastAPI()

@app.post("/register", response_model=ReturnUser)
async def register(user: CreateUser, db: Session = Depends(db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="This user already exists")
    
    new_user = User(username=user.username, password=hash(user.password), email=user.email, admin=user.admin)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
async def login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db)):
    user = get_user_by_username(db, data.username)
    if not user or not verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Login failed")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# Get
@app.get("/resources", response_model=list[ReturnResource])
async def get_resources(limit: int = 10, db: Session = Depends(db), cuser: User = Depends(get_curr_user)): # argument user upewnia się, że użytkownik jest zalogowany
    return db.query(Resource).limit(limit).all()

@app.get("/resources/{id}", response_model=ReturnResource)
async def get_resource(id: int, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource

@app.get("/reservations", response_model=list[ReturnReservation])
async def get_reservations(limit: int = 10, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    return db.query(Reservation).limit(limit).all()

@app.get("/reservations/{id}", response_model=ReturnReservation)
async def get_reservation(id: int, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    reservation = db.query(Resource).filter(Resource.id == id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Resource not found")

    return reservation


# Post
@app.post("/resources", response_model=ReturnResource)
async def create_resource(resource: CreateResource, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="No permissions")
    new_resource = Resource(**resource.model_dump())
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)

    return new_resource

@app.post("/reservations", response_model=ReturnReservation)
async def create_reservation(reservation: CreateReservation, bg: BackgroundTasks, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    duration = (reservation.end_date - reservation.start_date).total_seconds() / 60
    resource = db.query(Resource).filter(Resource.id == reservation.resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if duration < resource.min_duration or duration > resource.max_duration:
        raise HTTPException(status_code=400, detail="Duration greater or lesser than the set limits")
    if conflit(db, reservation.resource_id, reservation.start_date, reservation.end_date):
        raise HTTPException(status_code=400, detail="Reservation exists at the given datetime")
    if reservation.start_date.time().hour < 9 or reservation.end_date.time().hour > 18:
        raise HTTPException(status_code=400, detail="Reservation outside of available hours")

    new_reservation = Reservation(
        user_id=user.id,
        resource_id=reservation.resource_id,
        start_datetime=reservation.start_date,
        end_datetime=reservation.end_date
    )

    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    notify_time = new_reservation.start_date - timedelta(hours=1)
    if notify_time < datetime.now(timezone.utc):
        bg.add_task(send_email, user.email, f"Resource reservation reminder {resource.name} at {new_reservation.start_date}")

    return new_reservation


# Put
@app.put("/resources/{id}", response_model=ReturnResource)
async def update_resource(id: int, data: CreateResource, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="No permission")
    
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    for key, value in data.__dict__.items():
        setattr(resource, key, value)
    db.commit()
    db.refresh(resource)

    return resource
    
@app.put("/reservations/{id}", response_model=ReturnReservation)
async def update_reservation(id: int, data: CreateReservation, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    reservation = db.query(Reservation).filter(Reservation.id == id).first()
    duration = (reservation.end_date - reservation.start_date).total_seconds() / 60
    resource = db.query(Resource).filter(Resource.id == data.resource_id).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not user.admin and reservation.user_id != user.id:
        raise HTTPException(status_code=403, detail="No permissions")
    if conflit(db, data.resource_id, data.start_date, data.end_date, reservation_id=id):
        raise HTTPException(status_code=400, detail="Reservation exists at the given datetime")
    if duration < resource.min_duration or duration > resource.max_duration:
        raise HTTPException(status_code=400, detail="Duration greater or lesser than the set limits")
    
    reservation.resource_id = data.resource_id
    reservation.start_date = data.start_date
    reservation.end_date = data.end_date
    db.commit()
    db.refresh(reservation)

    return reservation


# Delete
@app.delete("/resources/{id}")
async def delete_resource(id: int, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    if not user.admin():
        raise HTTPException(status_code=403, detail="No permission")
    
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    db.delete(resource)
    db.commit()

    return {"message": "Deletion successful"}

@app.delete("/reservations/{id}")
async def delete_reservation(id: int, db: Session = Depends(db), user: User = Depends(get_curr_user)):
    reservation = db.query(Reservation).filter(Reservation.id == id).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not user.admin != "admin" and reservation.user_id != user.id:
        raise HTTPException(status_code=403, detail="Brak uprawnień")
    
    db.delete(reservation)
    db.commit()

    return {"message": "Deletion successful"}
