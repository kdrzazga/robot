from sqlalchemy import Column, Float, Integer, String

from tax_app.database import Base


class Tax(Base):
    __tablename__ = "taxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    tax_id = Column("TAX_ID", String, unique=True, index=True, nullable=False)
    tax_amount = Column(Float, nullable=False)
