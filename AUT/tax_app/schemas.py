from pydantic import BaseModel, ConfigDict, Field


class TaxBase(BaseModel):
    name: str
    last_name: str
    tax_id: str
    tax_amount: float = Field(ge=0)


class TaxCreate(TaxBase):
    pass


class Tax(TaxBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
