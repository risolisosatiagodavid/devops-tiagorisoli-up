import tomllib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from app.data_access import InventoryRepository
from app.middleware import request_timing_middleware
from app.schemas import Item, ItemUpdate

def get_project_version() -> str:
    # Busca pyproject.toml en la raíz (un nivel arriba de app/)
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "0.1.0-dev"
        
APP_VERSION = get_project_version()

app = FastAPI(
    title="Inventory API",
    description="API básica de gestión de inventario para TP DevOps",
    version=APP_VERSION,
)

app.middleware("http")(request_timing_middleware)

inventory_repository = InventoryRepository()

@app.get("/", status_code=200)
def read_root():
    return {"status": "healthy", "service": "inventory-api", "version": APP_VERSION}

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

@app.patch("/items/{item_id}", status_code=200)
def update_item(item_id: int, changes: ItemUpdate):
    update_data = changes.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un campo para actualizar")

    updated_item = inventory_repository.update(item_id, update_data)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return updated_item

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    deleted = inventory_repository.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return

