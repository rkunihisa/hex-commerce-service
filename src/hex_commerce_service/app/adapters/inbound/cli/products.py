from __future__ import annotations

import json
from decimal import Decimal

import typer

from hex_commerce_service.app.domain.entities import Product
from hex_commerce_service.app.domain.errors import DomainError
from hex_commerce_service.app.domain.value_objects import Money, Sku

from .container import get_services

app = typer.Typer()


@app.command("add")
def add_product(
    ctx: typer.Context,
    sku: str = typer.Option(..., "--sku", help="SKU code"),
    name: str = typer.Option(..., "--name", help="Product name"),
    price: str = typer.Option(..., "--price", help="Unit price (major)"),
    currency: str = typer.Option("USD", "--currency", help="Currency code (3 letters)"),
) -> None:
    svc = get_services()
    try:
        product = Product(
            sku=Sku(sku), name=name.strip(), unit_price=Money.from_major(Decimal(price), currency)
        )
        with svc.uow:
            svc.uow.products.add(product)
            svc.uow.commit()
        data = {
            "sku": product.sku.value,
            "name": product.name,
            "price": f"{product.unit_price.amount:.2f}",
            "currency": str(product.unit_price.currency),
        }
        if ctx.obj and ctx.obj.get("json"):
            typer.echo(json.dumps(data, ensure_ascii=False))
        else:
            typer.echo(f"Created product {data}")
    except DomainError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc


@app.command("get")
def get_product(ctx: typer.Context, sku: str = typer.Argument(..., help="SKU code")) -> None:
    svc = get_services()
    prod = svc.uow.products.get_by_sku(Sku(sku))
    if not prod:
        typer.secho("product not found", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)
    data = {
        "sku": prod.sku.value,
        "name": prod.name,
        "price": f"{prod.unit_price.amount:.2f}",
        "currency": str(prod.unit_price.currency),
    }
    if ctx.obj and ctx.obj.get("json"):
        typer.echo(json.dumps(data, ensure_ascii=False))
    else:
        typer.echo(data)


@app.command("list")
def list_products(ctx: typer.Context) -> None:
    svc = get_services()
    items = [
        {
            "sku": p.sku.value,
            "name": p.name,
            "price": f"{p.unit_price.amount:.2f}",
            "currency": str(p.unit_price.currency),
        }
        for p in svc.uow.products.list()
    ]
    if ctx.obj and ctx.obj.get("json"):
        typer.echo(json.dumps(items, ensure_ascii=False))
    else:
        for row in items:
            typer.echo(row)
