import json
import logging

import pytest
from fastapi.testclient import TestClient
from app.core.logging import JsonFormatter
from app.main import APP_VERSION
from app.main import app, inventory_repository


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def clean_repository(client):
    inventory_repository.clear()
    yield

@pytest.fixture
def created_item(client):
    payload = {"name": "Mouse gamer", "price": 100.0, "quantity": 10}
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    return response.json()

def test_root_serves_frontend(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'href="/static/styles.css"' in response.text
    assert 'src="/static/app.js"' in response.text
    assert 'id="refresh-products"' in response.text


def test_health_page(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'src="/static/health.js"' in response.text


def test_health_page_script_is_served(client):
    response = client.get("/static/health.js")

    assert response.status_code == 200
    assert "checkHealth" in response.text


def test_health_check(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "inventory-api",
        "version": APP_VERSION,
    }


def test_metrics_endpoint_exposes_http_requests(client):
    client.get("/items/99999")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert 'inventory_http_requests_total{method="GET",route="/items/{item_id}",status="404"}' in response.text
    assert "inventory_http_request_duration_seconds_bucket" in response.text
    assert 'route="/metrics"' not in response.text


def test_http_request_log_is_structured_json(client, caplog):
    with caplog.at_level(logging.INFO, logger="inventory_api"):
        response = client.get("/items/99999")

    assert response.status_code == 404
    record = next(
        record
        for record in caplog.records
        if record.name == "inventory_api"
        and record.getMessage() == "HTTP request completed"
    )
    event = json.loads(JsonFormatter().format(record))

    assert event["timestamp"]
    assert event["level"] == "INFO"
    assert event["path"] == "/items/99999"
    assert event["status_code"] == 404
    assert event["method"] == "GET"
    assert event["duration_seconds"] >= 0
    assert len(event["trace_id"]) == 32
    assert len(event["span_id"]) == 16
    assert int(event["trace_id"], 16) > 0
    assert int(event["span_id"], 16) > 0


def test_inventory_ui_serves_frontend(client):
    response = client.get("/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'href="/static/styles.css"' in response.text
    assert 'src="/static/app.js"' in response.text

def test_inventory_ui_serves_static_assets(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "loadProducts" in response.text

#POST
def test_create_item_success(client):
    item_data = {"name": "Teclado Mecanico", "price": 120.0, "quantity": 5}
    response = client.post("/items", json=item_data)

    assert response.status_code == 201
    res = response.json()
    assert "id" in res
    assert res["item"]["name"] == item_data["name"]
    assert client.get("/items").json()[str(res["id"])] == item_data

def test_create_item_invalid_data(client):
    item_data = {"name": "Mousepad gamer", "price": "invalid_price", "quantity": 10}
    response = client.post("/items", json=item_data)

    assert response.status_code == 422

#GET
def test_get_items_success(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_get_item_success(client, created_item):
    item_id = created_item["id"]
    response = client.get(f"/items/{item_id}")
    
    assert response.status_code == 200
    assert response.json() == created_item["item"]

def test_get_item_not_found(client):
    response = client.get("/items/99999")  
    assert response.status_code == 404
    assert response.json() == {"detail": "Item no encontrado"}


#PATCH
def test_update_item_success(client, created_item):
    item_id = created_item["id"]
    response = client.patch(f"/items/{item_id}", json={"price": 125.0})

    assert response.status_code == 200
    assert response.json() == {
        "name": "Mouse gamer",
        "price": 125.0,
        "quantity": 10,
    }

def test_update_item_not_found(client):
    response = client.patch("/items/99999", json={"price": 125.0})

    assert response.status_code == 404
    assert response.json() == {"detail": "Item no encontrado"}

def test_update_item_without_fields(client, created_item):
    item_id = created_item["id"]
    response = client.patch(f"/items/{item_id}", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "Debe enviar al menos un campo para actualizar"}

#DELETE
def test_delete_item_success(client, created_item):
    item_id = created_item["id"]
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204

def test_delete_item_not_found(client):
    response = client.delete("/items/99999")  
    assert response.status_code == 404
    assert response.json() == {"detail": "Item no encontrado"}
