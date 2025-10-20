from __future__ import annotations

import pytest

from hex_commerce_service.app.acl.errors import MappingError
from hex_commerce_service.app.acl.mapping import map_external_order_to_command
from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.use_cases.place_order import PlaceOrderUseCase
from hex_commerce_service.app.domain.entities import Product
from hex_commerce_service.app.domain.value_objects import Money, Sku


def _seed_products(uow: InMemoryUnitOfWork) -> None:
    uow.products.add(Product(sku=Sku("ABC-1"), name="W", unit_price=Money.from_major(10, "USD")))
    uow.products.add(Product(sku=Sku("ABC-2"), name="G", unit_price=Money.from_major(5, "USD")))


def test_external_order_mapping_and_place_success() -> None:
    uow = InMemoryUnitOfWork()
    _seed_products(uow)
    idg = InMemoryIdGenerator()
    uc = PlaceOrderUseCase(uow=uow, id_gen=idg)

    external_payload = {
        "orderItems": [
            {"product_code": "abc-1", "qty": 2},
            {"product_code": "ABC-2", "qty": 3},
        ],
        "currency": "usd",
    }

    cmd = map_external_order_to_command(external_payload)
    res = uc.execute(cmd)

    assert res.total.currency == "USD"
    assert f"{res.total.amount:.2f}" == "35.00"


@pytest.mark.parametrize(
    "payload,expected_paths",
    [
        ({"orderItems": []}, ["orderItems"]),  # empty
        ({"orderItems": [{"product_code": "???", "qty": 1}]}, ["orderItems.0.product_code"]),  # bad sku
        ({"orderItems": [{"product_code": "ABC-1", "qty": 0}]}, ["orderItems.0.qty"]),  # qty <= 0
        ({"orderItems": [{"qty": 1}]}, ["orderItems.0.product_code"]),  # missing sku
        ({"currency": "us", "orderItems": [{"product_code": "ABC-1", "qty": 1}]}, ["__root__"]),  # currency bad length (surface as model error)
    ],
)
def test_external_order_mapping_failures(payload, expected_paths) -> None:
    try:
        _ = map_external_order_to_command(payload)
        assert False, "should raise MappingError"
    except MappingError as me:
        joined = "\n".join(i.path for i in me.issues)
        for p in expected_paths:
            assert p.split(".")[0] in joined or p in joined
