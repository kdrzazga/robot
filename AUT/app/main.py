from contextlib import asynccontextmanager
from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin,
)
from app.database import Base, SessionLocal, engine, get_db
from app.seed import seed_data

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Customer DB AUT", version="1.0.0", lifespan=lifespan)


@app.post("/token", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/reset", tags=["admin"])
def reset_database(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Wipe and re-seed the in-memory DB. Handy for Robot Framework suites
    that need a known starting state before each test/suite."""
    seed_data(db)
    return {"status": "reset"}


# --- Address endpoints ---

@app.get("/addresses", response_model=List[schemas.Address], tags=["addresses"])
def list_addresses(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(models.Address).all()


@app.get("/addresses/{address_id}", response_model=schemas.Address, tags=["addresses"])
def get_address(address_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    address = db.query(models.Address).filter(models.Address.id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@app.post("/addresses", response_model=schemas.Address, status_code=201, tags=["addresses"])
def create_address(
    address: schemas.AddressCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_address = models.Address(**address.model_dump())
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address


@app.put("/addresses/{address_id}", response_model=schemas.Address, tags=["addresses"])
def update_address(
    address_id: int,
    address: schemas.AddressCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_address = db.query(models.Address).filter(models.Address.id == address_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    for key, value in address.model_dump().items():
        setattr(db_address, key, value)
    db.commit()
    db.refresh(db_address)
    return db_address


@app.delete("/addresses/{address_id}", status_code=204, tags=["addresses"])
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_address = db.query(models.Address).filter(models.Address.id == address_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(db_address)
    db.commit()
    return None


# --- Person endpoints ---

@app.get("/persons", response_model=List[schemas.PersonWithAddress], tags=["persons"])
def list_persons(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(models.Person).all()


@app.get("/persons/{person_id}", response_model=schemas.PersonWithAddress, tags=["persons"])
def get_person(person_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@app.post("/persons", response_model=schemas.Person, status_code=201, tags=["persons"])
def create_person(
    person: schemas.PersonCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    address = db.query(models.Address).filter(models.Address.id == person.address_id).first()
    if not address:
        raise HTTPException(status_code=400, detail="address_id does not reference an existing address")
    db_person = models.Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@app.put("/persons/{person_id}", response_model=schemas.Person, tags=["persons"])
def update_person(
    person_id: int,
    person: schemas.PersonCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if not db_person:
        raise HTTPException(status_code=404, detail="Person not found")
    address = db.query(models.Address).filter(models.Address.id == person.address_id).first()
    if not address:
        raise HTTPException(status_code=400, detail="address_id does not reference an existing address")
    for key, value in person.model_dump().items():
        setattr(db_person, key, value)
    db.commit()
    db.refresh(db_person)
    return db_person


@app.delete("/persons/{person_id}", status_code=204, tags=["persons"])
def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_person = db.query(models.Person).filter(models.Person.id == person_id).first()
    if not db_person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(db_person)
    db.commit()
    return None
