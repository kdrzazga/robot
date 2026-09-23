from sqlalchemy.orm import Session

from app import models


def seed_data(db: Session) -> None:
    """Wipe and repopulate the DB with a fixed, known dataset."""
    db.query(models.Person).delete()
    db.query(models.Address).delete()
    db.commit()

    addresses = [
        models.Address(street="1 Main St", city="Warsaw", zip_code="00-001", country="Poland"),
        models.Address(street="22 Oak Ave", city="Krakow", zip_code="30-002", country="Poland"),
        models.Address(street="5 Baker St", city="London", zip_code="NW1 6XE", country="United Kingdom"),
    ]
    db.add_all(addresses)
    db.commit()
    for a in addresses:
        db.refresh(a)

    persons = [
        models.Person(name="John", last_name="Smith", tax_id="TAX-1001", address_id=addresses[0].id),
        models.Person(name="Anna", last_name="Kowalska", tax_id="TAX-1002", address_id=addresses[1].id),
        models.Person(name="Sherlock", last_name="Holmes", tax_id="TAX-1003", address_id=addresses[2].id),
    ]
    db.add_all(persons)
    db.commit()
