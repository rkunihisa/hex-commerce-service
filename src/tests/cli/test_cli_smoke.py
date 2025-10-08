from __future__ import annotations

import json

from typer.testing import CliRunner

from hex_commerce_service.app.adapters.inbound.cli.app import app


runner = CliRunner()


def test_cli_end_to_end_smoke_json_output() -> None:
    # add products
    r = runner.invoke(app, ["--json", "products", "add", "--sku", "ABC-1", "--name", "Widget", "--price", "10.00", "--currency", "USD"])
    assert r.exit_code == 0, r.stdout
    r = runner.invoke(app, ["--json", "products", "add", "--sku", "ABC-2", "--name", "Gadget", "--price", "5.00", "--currency", "USD"])
    assert r.exit_code == 0, r.stdout

    # upsert inventory
    r = runner.invoke(app, ["--json", "inventory", "upsert", "--location", "default", "-i", "ABC-1=5", "-i", "ABC-2=7"])
    assert r.exit_code == 0, r.stdout
    inv = json.loads(r.stdout.strip())
    assert inv["location"] == "default"
    items = {it["sku"]: it["on_hand"] for it in inv["items"]}
    assert items["ABC-1"] == 5 and items["ABC-2"] == 7

    # place order
    r = runner.invoke(app, ["--json", "orders", "place", "-i", "ABC-1:2", "-i", "ABC-2:3"])
    assert r.exit_code == 0, r.stdout
    order = json.loads(r.stdout.strip())
    assert order["total"] == {"currency": "USD", "amount": "35.00"}
    order_id = order["order_id"]

    # allocate
    r = runner.invoke(app, ["--json", "orders", "allocate", "--order-id", order_id])
    assert r.exit_code == 0, r.stdout
    res = json.loads(r.stdout.strip())
    assert res["status"] == "allocated"

    # inventory decreased
    r = runner.invoke(app, ["--json", "inventory", "get", "default"])
    assert r.exit_code == 0, r.stdout
    inv2 = json.loads(r.stdout.strip())
    items2 = {it["sku"]: it["on_hand"] for it in inv2["items"]}
    assert items2["ABC-1"] == 3 and items2["ABC-2"] == 4
