from pydantic import BaseModel, ConfigDict


class AddressBase(BaseModel):
    street: str
    city: str
    zip_code: str
    country: str


class AddressCreate(AddressBase):
    pass


class Address(AddressBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PersonBase(BaseModel):
    name: str
    last_name: str
    tax_id: str
    address_id: int


class PersonCreate(PersonBase):
    pass


class Person(PersonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PersonWithAddress(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    last_name: str
    tax_id: str
    address: Address


class TaxRecord(BaseModel):
    """A record as returned by the TaxInformation service."""
    id: int
    name: str
    last_name: str
    tax_id: str
    tax_amount: float


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None
