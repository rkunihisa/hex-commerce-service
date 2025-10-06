from __future__ import annotations

import json

import typer

from . import orders as orders_cmd
from . import products as products_cmd
from . import inventory as inventory_cmd

app = typer.Typer(help="Hex Commerce CLI (in-memory)")

# サブコマンドを登録
app.add_typer(products_cmd.app, name="products", help="Manage products")
app.add_typer(inventory_cmd.app, name="inventory", help="Manage inventory")
app.add_typer(orders_cmd.app, name="orders", help="Manage orders")


@app.callback()
def main(
    ctx: typer.Context,
    *,
    json_output: bool = typer.Option(
        "--json",
        help="Output JSON where applicable",
        is_flag=True,
        show_default=False
    )
) -> None:
    ctx.obj = {"json": bool(json_output)}


def _echo(ctx: typer.Context, data: object) -> None:
    if ctx.obj and ctx.obj.get("json"):
        typer.echo(json.dumps(data, ensure_ascii=False))
    else:
        typer.echo(data)


if __name__ == "__main__":
    app()
