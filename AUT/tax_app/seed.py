from sqlalchemy.orm import Session

from tax_app import models


def seed_data(db: Session) -> None:
    """Wipe and repopulate the DB with a fixed, known dataset.

    The first three TAX_IDs match the persons seeded by the customer DB
    service; TAX-1004 deliberately has no matching person."""
    db.query(models.Tax).delete()
    db.commit()

    db.add_all([
        models.Tax(name="John", last_name="Smith", tax_id="TAX-1001", tax_amount=1250.00),
        models.Tax(name="Anna", last_name="Kowalska", tax_id="TAX-1002", tax_amount=980.50),
        models.Tax(name="Sherlock", last_name="Holmes", tax_id="TAX-1003", tax_amount=3400.00),
        models.Tax(name="Jane", last_name="Doe", tax_id="TAX-1004", tax_amount=0.00),
    ])
    db.commit()
