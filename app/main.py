from fastapi import FastAPI, HTTPException

from app.data_access import InventoryRepository
from app.middleware import request_timing_middleware
from app.schemas import Item

app = FastAPI(
    title="Inventory API",
    description="API básica de gestión de inventario para TP DevOps",
    version="0.1.0",
)
app.middleware("http")(request_timing_middleware)

inventory_repository = InventoryRepository()

@app.get("/", status_code=200)
def read_root():
    return {"status": "healthy", "service": "inventory-api"}

@app.get("/items", status_code=200)
def get_items():
    return inventory_repository.get_all()

@app.get("/items/{item_id}", status_code=200)
def get_item(item_id: int):
    item = inventory_repository.get_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item

@app.post("/items", status_code=201)
def create_item(item: Item):
    new_id = inventory_repository.create(item)
    return {"id": new_id, "item": item}

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    deleted = inventory_repository.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return

