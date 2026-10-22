from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import tomllib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.logging import configure_logging
from app.core.metrics import PrometheusMetricsMiddleware, metrics_response
from app.core.telemetry import instrument_app, setup_telemetry
from app.data_access import InventoryRepository
from app.database import engine, init_db
from app.schemas import Item, ItemUpdate

print("esto se va a descontrolar")

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

configure_logging()
provider = setup_telemetry(engine, service_version=APP_VERSION)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield
    if provider:
        provider.shutdown()


app = FastAPI(
    title="Inventory API",
    description="API básica de gestión de inventario para TP DevOps",
    version=APP_VERSION,
    lifespan=lifespan,
)

instrument_app(app)
app.add_middleware(PrometheusMetricsMiddleware)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

inventory_repository = InventoryRepository()


@app.get("/ui", include_in_schema=False)
def inventory_ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", include_in_schema=False)
def health_page():
    return FileResponse(STATIC_DIR / "health.html")


@app.get("/healthz", status_code=200)
def health_check():
    return {"status": "healthy", "service": "inventory-api", "version": APP_VERSION}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_response()


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
