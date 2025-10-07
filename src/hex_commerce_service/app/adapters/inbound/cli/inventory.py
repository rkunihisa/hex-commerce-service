from __future__ import annotations

import json

import typer

from hex_commerce_service.app.domain.entities import Inventory
from hex_commerce_service.app.domain.errors import DomainError, ValidationError
from hex_commerce_service.app.domain.value_objects import Sku

from .container import get_services

app = typer.Typer()


def _parse_item(value: str) -> tuple[Sku, int]:
    sep = "=" if "=" in value else ":"
    try:
        sku_raw, qty_raw = value.split(sep, 1)
        sku = Sku(sku_raw)
        qty = int(qty_raw)
    except Exception as exc:
        raise ValidationError(f"invalid item format: {value!r}; use SKU=QTY") from exc
    if qty < 0:
        raise ValidationError("on_hand must be >= 0")
    return sku, qty


@app.command("upsert")
def upsert_inventory(
    ctx: typer.Context,
    location: str = typer.Option("default", "--location", "-l", help="Inventory location"),
    item: list[str] | None = None,
) -> None:
    if item is None:
        item = typer.Option(..., "--item", "-i", help="Stock item (SKU=QTY), repeatable")

    svc = get_services()
    try:
        inv = Inventory(location=location)
        for it in item:
            sku, qty = _parse_item(it)
            inv.set_on_hand(sku, qty)
        with svc.uow:
            svc.uow.inventories.upsert(inv)
            svc.uow.commit()
        rows = [{"sku": s.value, "on_hand": inv.available(s)} for s in inv._on_hand]  # noqa: SLF001
        if ctx.obj and ctx.obj.get("json"):
            typer.echo(json.dumps({"location": location, "items": rows}, ensure_ascii=False))
        else:
            typer.echo({"location": location, "items": rows})
    except (DomainError, ValidationError) as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc


@app.command("get")
def get_inventory(ctx: typer.Context, location: str = typer.Argument("default")) -> None:
    svc = get_services()
    inv = svc.uow.inventories.get(location)
    if not inv:
        typer.secho("inventory not found", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)
    rows = [{"sku": s.value, "on_hand": inv.available(s)} for s in inv._on_hand]  # noqa: SLF001
    if ctx.obj and ctx.obj.get("json"):
        typer.echo(json.dumps({"location": location, "items": rows}, ensure_ascii=False))
    else:
        typer.echo({"location": location, "items": rows})
