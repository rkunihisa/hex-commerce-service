from __future__ import annotations

import json

import typer

from hex_commerce_service.app.application.use_cases.allocate_stock import (
    AllocateStockCommand,
    AllocateStockUseCase,
)
from hex_commerce_service.app.application.use_cases.place_order import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.domain.errors import DomainError, OutOfStock, ValidationError
from hex_commerce_service.app.domain.value_objects import OrderId, Sku

from .container import get_services

app = typer.Typer()


def _parse_order_item(value: str) -> NewOrderItem:
    sep = ":" if ":" in value else "="
    try:
        sku_raw, qty_raw = value.split(sep, 1)
        sku = Sku(sku_raw)
        qty = int(qty_raw)
    except Exception as exc:
        raise ValidationError(f"invalid item format: {value!r}; use SKU:QTY") from exc
    if qty <= 0:
        raise ValidationError("quantity must be > 0")
    return NewOrderItem(sku=sku, quantity=qty)


@app.command("place")
def place_order(ctx: typer.Context, item: list[str] | None = None) -> None:
    if item is None:
        item = typer.Option(..., "--item", "-i", help="Order item (SKU:QTY), repeatable")
    svc = get_services()
    try:
        uc = PlaceOrderUseCase(uow=svc.uow, id_gen=svc.id_gen)
        cmd = PlaceOrderCommand(items=[_parse_order_item(x) for x in item])
        res = uc.execute(cmd)
        data = {
            "order_id": res.order_id,
            "total": {"currency": str(res.total.currency), "amount": f"{res.total.amount:.2f}"},
        }
        if ctx.obj and ctx.obj.get("json"):
            typer.echo(json.dumps(data, ensure_ascii=False))
        else:
            typer.echo(data)
    except (DomainError, ValidationError) as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc


@app.command("allocate")
def allocate(ctx: typer.Context, order_id: str = typer.Option(..., "--order-id", "-o", help="Order ID")) -> None:
    svc = get_services()
    try:
        uc = AllocateStockUseCase(uow=svc.uow)
        uc.execute(AllocateStockCommand(order_id=OrderId.parse(order_id)))
        if ctx.obj and ctx.obj.get("json"):
            typer.echo(json.dumps({"status": "allocated", "order_id": order_id}, ensure_ascii=False))
        else:
            typer.echo({"status": "allocated", "order_id": order_id})
    except (OutOfStock, DomainError, ValidationError) as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc
