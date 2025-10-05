from __future__ import annotations

import asyncio
import os
from typing import Dict

import pytest
from httpx import ASGITransport, AsyncClient

from hex_commerce_service.app.adapters.inbound.api.app import create_app

if os.getenv("GITHUB_ACTIONS") == "true":
    pytest.skip("Skip API test on GitHub Actions CI", allow_module_level=True)


pytestmark = pytest.mark.asyncio


async def _issue_token(ac: AsyncClient, roles: list[str]) -> str:
    r = await ac.post("/auth/token/test", json={"sub": "tester", "roles": roles})
    assert r.status_code == 200, r.text
    access_token: str = r.json()["access_token"]
    return access_token

async def test_authz_enforced_and_flow_succeeds() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        user_tok = await _issue_token(ac, ["user"])
        admin_tok = await _issue_token(ac, ["admin"])

        # 401 when no token
        r = await ac.post("/products", json={"sku": "X", "name": "X", "price": "1.00", "currency": "USD"})
        assert r.status_code == 401

        # 403 for user creating product
        r = await ac.post(
            "/products",
            json={"sku": "ABC-1", "name": "W", "price": "10.00", "currency": "USD"},
            headers={"Authorization": f"Bearer {user_tok}"},
        )
        assert r.status_code == 403

        # 201 for admin creating product
        for sku, name, price in [("ABC-1", "W", "10.00"), ("ABC-2", "G", "5.00")]:
            r = await ac.post(
                "/products",
                json={"sku": sku, "name": name, "price": price, "currency": "USD"},
                headers={"Authorization": f"Bearer {admin_tok}"},
            )
            assert r.status_code == 201, r.text

        # upsert inventory (admin)
        r = await ac.put(
            "/inventory/default",
            json={"location": "default", "items": [{"sku": "ABC-1", "on_hand": 5}, {"sku": "ABC-2", "on_hand": 7}]},
            headers={"Authorization": f"Bearer {admin_tok}"},
        )
        assert r.status_code == 200, r.text

        # user can place order
        r = await ac.post(
            "/orders",
            json={"items": [{"sku": "ABC-1", "quantity": 2}, {"sku": "ABC-2", "quantity": 3}]},
            headers={"Authorization": f"Bearer {user_tok}"},
        )
        assert r.status_code == 201, r.text
        order_id = r.json()["order_id"]

        # user cannot allocate
        r = await ac.post(f"/orders/{order_id}/allocate", headers={"Authorization": f"Bearer {user_tok}"})
        assert r.status_code == 403

        # admin allocates
        r = await ac.post(f"/orders/{order_id}/allocate", headers={"Authorization": f"Bearer {admin_tok}"})
        assert r.status_code == 200

        # inventory GET requires user
        r = await ac.get("/inventory/default", headers={"Authorization": f"Bearer {user_tok}"})
        assert r.status_code == 200
        items: Dict[str, int] = {it["sku"]: it["on_hand"] for it in r.json()["items"]}
        assert items["ABC-1"] == 3 and items["ABC-2"] == 4


async def test_revocation_blocks_further_access() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        tok = await _issue_token(ac, ["admin"])
        # Revoke the token
        r = await ac.post("/auth/revoke", json={"token": tok})
        assert r.status_code == 200

        # Now any admin-only call must fail with 401
        r = await ac.post(
            "/products",
            json={"sku": "X", "name": "X", "price": "1.00", "currency": "USD"},
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert r.status_code == 401
