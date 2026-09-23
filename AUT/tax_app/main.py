from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import auth
from app.auth import get_current_user, require_admin
from tax_app import models, schemas
from tax_app.database import Base, SessionLocal, engine, get_db
from tax_app.seed import seed_data

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="TaxInformation AUT", version="1.0.0", lifespan=lifespan)

# The UI is served by the customer DB service on another port, so every call
# here is cross-origin. Wide open on purpose: this is a throwaway AUT.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Same users and signing key as the customer DB service, so one token works on both.
app.include_router(auth.router)


@app.post("/reset", tags=["admin"])
def reset_database(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Wipe and re-seed the in-memory DB to a known state."""
    seed_data(db)
    return {"status": "reset"}


# --- Tax endpoints ---

def _check_unique_tax_id(db: Session, tax_id: str, record_id: int | None = None):
    same_tax_id = db.query(models.Tax).filter(
        models.Tax.tax_id == tax_id, models.Tax.id != record_id
    ).first()
    if same_tax_id:
        raise HTTPException(status_code=400, detail="tax_id already exists")


@app.get("/taxes", response_model=List[schemas.Tax], tags=["taxes"])
def list_taxes(
    tax_id: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """List all tax records, or only the one matching `?tax_id=`."""
    query = db.query(models.Tax)
    if tax_id is not None:
        query = query.filter(models.Tax.tax_id == tax_id)
    return query.all()


@app.get("/taxes/{tax_record_id}", response_model=schemas.Tax, tags=["taxes"])
def get_tax(tax_record_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    tax = db.query(models.Tax).filter(models.Tax.id == tax_record_id).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax record not found")
    return tax


@app.post("/taxes", response_model=schemas.Tax, status_code=201, tags=["taxes"])
def create_tax(
    tax: schemas.TaxCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    _check_unique_tax_id(db, tax.tax_id)
    db_tax = models.Tax(**tax.model_dump())
    db.add(db_tax)
    db.commit()
    db.refresh(db_tax)
    return db_tax


@app.put("/taxes/{tax_record_id}", response_model=schemas.Tax, tags=["taxes"])
def update_tax(
    tax_record_id: int,
    tax: schemas.TaxCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_tax = db.query(models.Tax).filter(models.Tax.id == tax_record_id).first()
    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax record not found")
    _check_unique_tax_id(db, tax.tax_id, tax_record_id)
    for key, value in tax.model_dump().items():
        setattr(db_tax, key, value)
    db.commit()
    db.refresh(db_tax)
    return db_tax


@app.delete("/taxes/{tax_record_id}", status_code=204, tags=["taxes"])
def delete_tax(
    tax_record_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db_tax = db.query(models.Tax).filter(models.Tax.id == tax_record_id).first()
    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax record not found")
    db.delete(db_tax)
    db.commit()
    return None
