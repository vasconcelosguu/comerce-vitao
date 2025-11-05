from fastapi.testclient import TestClient
from app.main import app

def test_order_flow():
    client = TestClient(app)

    r = client.post("/users/", json={"name": "Ana", "email": "ana@example.com", "password": "123456"})
    assert r.status_code == 201
    user_id = r.json()["id"]

    r = client.post("/categories/", json={"name": "Eletronicos"})
    assert r.status_code == 201

    p1 = client.post("/products/", json={"name": "Mouse", "description": "", "price": 50.0, "stock": 5, "category_id": 1})
    p2 = client.post("/products/", json={"name": "Teclado", "description": "", "price": 150.0, "stock": 3, "category_id": 1})
    assert p1.status_code == 201 and p2.status_code == 201

    pid1 = p1.json()["id"]; pid2 = p2.json()["id"]

    order_payload = {
        "user_id": user_id,
        "items": [
            {"product_id": pid1, "quantity": 2},
            {"product_id": pid2, "quantity": 1},
        ],
    }
    r = client.post("/orders/", json=order_payload)

    if r.status_code != 201:
        print("ERRO /orders:", r.text)

    assert r.status_code == 201
    data = r.json()
    assert data["user_id"] == user_id
    assert len(data["items"]) == 2
    assert abs(data["total"] - 250.0) < 1e-6

    prods = client.get("/products/").json()
    m = [p for p in prods if p["name"] == "Mouse"][0]
    t = [p for p in prods if p["name"] == "Teclado"][0]
    assert m["stock"] == 3
    assert t["stock"] == 2