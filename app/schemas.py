from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    quantity: int

class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    quantity: int | None = None
