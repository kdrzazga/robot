from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.auth import get_current_user, require_admin
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

# Lets the UI call the API when index.html is opened from disk or another
# port. Wide open on purpose: this is a throwaway application-under-test.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")


app.include_router(auth.router)


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

def _check_person_references(db: Session, person: schemas.PersonCreate, person_id: int | None = None):
    address = db.query(models.Address).filter(models.Address.id == person.address_id).first()
    if not address:
        raise HTTPException(status_code=400, detail="address_id does not reference an existing address")
    same_tax_id = db.query(models.Person).filter(
        models.Person.tax_id == person.tax_id, models.Person.id != person_id
    ).first()
    if same_tax_id:
        raise HTTPException(status_code=400, detail="tax_id is already used by another person")


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
    _check_person_references(db, person)
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
    _check_person_references(db, person, person_id)
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
