import pytest
from fastapi.testclient import TestClient

from app.main import app, inventory_repository


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_repository():
    inventory_repository._items.clear()
    yield

@pytest.fixture
def created_item(client):
    payload = {"name": "Mouse gamer", "price": 100.0, "quantity": 10}
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    return response.json()


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "inventory-api"}
    assert "x-process-time" in response.headers


def test_create_item_success(client):
    item_data = {"name": "Teclado Mecanico", "price": 120.0, "quantity": 5}
    response = client.post("/items", json=item_data)

    assert response.status_code == 201
    res = response.json()
    assert "id" in res
    assert res["item"]["name"] == item_data["name"]
    assert "x-process-time" in response.headers

def test_create_item_invalid_data(client):
    item_data = {"name": "Mousepad gamer", "price": "invalid_price", "quantity": 10}
    response = client.post("/items", json=item_data)

    assert response.status_code == 422
    assert "x-process-time" in response.headers


def test_get_items_success(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "x-process-time" in response.headers

def test_get_item_success(client, created_item):
    item_id = created_item["id"]
    response = client.get(f"/items/{item_id}")
    
    assert response.status_code == 200
    assert response.json() == created_item["item"]
    assert "x-process-time" in response.headers

def test_get_item_not_found(client):
    response = client.get("/items/99999")  
    assert response.status_code == 404
    assert response.json() == {"detail": "Item no encontrado"}
    assert "x-process-time" in response.headers


def test_delete_item_success(client, created_item):
    item_id = created_item["id"]
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204
    assert "x-process-time" in response.headers

def test_delete_item_not_found(client):
    response = client.delete("/items/99999")  
    assert response.status_code == 404
    assert response.json() == {"detail": "Item no encontrado"}
    assert "x-process-time" in response.headers