from __future__ import annotations

import os

import pytest
from httpx import AsyncClient, ASGITransport

from hex_commerce_service.app.adapters.inbound.api.app import create_app

if os.getenv("GITHUB_ACTIONS") == "true":
    pytest.skip("Skip API test on GitHub Actions CI", allow_module_level=True)


pytestmark = pytest.mark.asyncio



async def test_place_order_and_allocate_success() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        # トークン発行
        resp = await ac.post(
            "/auth/token/test",
            json={"sub": "test-user", "roles": ["admin", "user"]}  # 両方付与
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # seed products
        r = await ac.post(
            "/products",
            json={"sku": "ABC-1", "name": "Widget", "price": "10.00", "currency": "USD"},
            headers=headers
        )
        assert r.status_code == 201
        r = await ac.post(
            "/products",
            json={"sku": "ABC-2", "name": "Gadget", "price": "5.00", "currency": "USD"},
            headers=headers
        )
        assert r.status_code == 201

        # seed inventory
        r = await ac.put(
            "/inventory/default",
            json={"location": "default", "items": [{"sku": "ABC-1", "on_hand": 5}, {"sku": "ABC-2", "on_hand": 7}]},
            headers=headers
        )
        assert r.status_code == 200

        # place order
        r = await ac.post(
            "/orders",
            json={"items": [{"sku": "ABC-1", "quantity": 2}, {"sku": "ABC-2", "quantity": 3}]},
            headers=headers
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["total"] == {"currency": "USD", "amount": "35.00"}
        order_id = data["order_id"]

        # allocate
        r = await ac.post(f"/orders/{order_id}/allocate", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "allocated"

        # inventory decreased
        r = await ac.get("/inventory/default", headers=headers)
        assert r.status_code == 200
        items = {it["sku"]: it["on_hand"] for it in r.json()["items"]}
        assert items["ABC-1"] == 3
        assert items["ABC-2"] == 4


async def test_validation_and_error_mapping() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        # トークン発行
        resp = await ac.post(
            "/auth/token/test",
            json={"sub": "test-user", "roles": ["admin", "user"]}  # 両方付与
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # seed one product / no inventory
        await ac.post(
            "/products",
            json={"sku": "ABC-1", "name": "W", "price": "10.00", "currency": "USD"},
            headers=headers
        )

        # place order with unknown sku -> 400
        r = await ac.post("/orders", json={"items": [{"sku": "NOPE", "quantity": 1}]}, headers=headers)
        assert r.status_code == 400

        # place order for ABC-1
        r = await ac.post("/orders", json={"items": [{"sku": "ABC-1", "quantity": 5}]}, headers=headers)
        oid = r.json()["order_id"]

        # allocate without inventory -> 400 (validation error)
        r = await ac.post(f"/orders/{oid}/allocate", headers=headers)
        assert r.status_code == 400

        # set insufficient inventory and try allocate -> 409
        await ac.put("/inventory/default", json={"location": "default", "items": [{"sku": "ABC-1", "on_hand": 3}]}, headers=headers)
        r = await ac.post(f"/orders/{oid}/allocate", headers=headers)
        assert r.status_code == 409
