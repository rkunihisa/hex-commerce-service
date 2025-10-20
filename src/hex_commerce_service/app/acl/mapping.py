from __future__ import annotations

from pydantic import ValidationError

from hex_commerce_service.app.acl.dto_external import ExternalInventoryPayload, ExternalOrderPayload
from hex_commerce_service.app.acl.errors import MappingError, MappingIssue
from hex_commerce_service.app.application.use_cases.place_order import NewOrderItem, PlaceOrderCommand
from hex_commerce_service.app.domain.entities import Inventory
from hex_commerce_service.app.domain.value_objects import Sku


def _issues_from_pydantic(err: ValidationError) -> list[MappingIssue]:
    issues: list[MappingIssue] = []
    for e in err.errors():
        loc = ".".join(str(x) for x in e.get("loc", []))
        msg = e.get("msg", "invalid value")
        typ = e.get("type", "value_error")
        issues.append(MappingIssue(path=loc, code=typ, message=msg))
    return issues


def map_external_order_to_command(payload: dict) -> PlaceOrderCommand:
    try:
        ext = ExternalOrderPayload.model_validate(payload)
    except ValidationError as ve:
        raise MappingError(_issues_from_pydantic(ve)) from ve

    items: list[NewOrderItem] = []
    sku_errors: list[MappingIssue] = []
    for idx, it in enumerate(ext.orderItems):
        try:
            items.append(NewOrderItem(sku=Sku(it.product_code), quantity=it.qty))
        except ValueError as exc:
            sku_errors.append(
                MappingIssue(
                    path=f"orderItems.{idx}.product_code",
                    code="invalid_sku",
                    message=str(exc),
                )
            )
    if sku_errors:
        raise MappingError(sku_errors)

    if not items:
        raise MappingError([MappingIssue(path="orderItems", code="value_error.min_items", message="must contain at least one item")])

    return PlaceOrderCommand(items=items)


def map_external_inventory_to_domain(payload: dict) -> Inventory:
    try:
        ext = ExternalInventoryPayload.model_validate(payload)
    except ValidationError as ve:
        raise MappingError(_issues_from_pydantic(ve)) from ve

    inv = Inventory(location=ext.warehouse)
    sku_errors: list[MappingIssue] = []
    for idx, row in enumerate(ext.stock):
        try:
            inv.set_on_hand(Sku(row.code), row.count)
        except ValueError as exc:
            sku_errors.append(
                MappingIssue(
                    path=f"stock.{idx}.code",
                    code="invalid_sku",
                    message=str(exc),
                )
            )
    if sku_errors:
        raise MappingError(sku_errors)
    return inv
