from practice_target import load

import json

import pytest

pytest.importorskip("pydantic", reason="run with: --with fastapi --with httpx")
from pydantic import ValidationError

m = load("p22_pydantic")

ORDER = {
    "order_id": "o1",
    "customer": "ana",
    "items": [
        {"sku": "tea", "qty": 2, "unit_price": 1.5},
        {"sku": "mug", "qty": 1, "unit_price": 3},
    ],
}


def test_total_is_computed_and_dumped():
    order = m.Order.model_validate(ORDER)
    assert order.total == 6.0
    assert order.model_dump()["total"] == 6.0
    tiny = m.Order.model_validate({**ORDER, "items": [{"sku": "x", "qty": 3, "unit_price": 0.1}]})
    assert tiny.total == 0.3  # 3 * 0.1 is 0.30000000000000004 before rounding


def test_parse_order_lax_mode_and_nesting():
    raw = json.dumps({**ORDER, "items": [{"sku": "tea", "qty": "2", "unit_price": "1.5"}]})
    order = m.parse_order(raw)
    assert isinstance(order.items[0], m.LineItem)
    assert (order.items[0].qty, order.items[0].unit_price) == (2, 1.5)
    assert order.note is None


def test_parse_order_strict_mode_rejects_strings():
    raw = json.dumps({**ORDER, "items": [{"sku": "tea", "qty": "2", "unit_price": 1.5}]})
    with pytest.raises(ValidationError, match="int_type"):
        m.parse_order(raw, strict=True)


def test_parse_order_forbids_extra_keys_and_is_frozen():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        m.parse_order(json.dumps({**ORDER, "coupon": "FREE"}))
    order = m.parse_order(json.dumps(ORDER))
    with pytest.raises(ValidationError, match="frozen_instance"):
        order.customer = "bob"


def test_to_public_json():
    user = m.PublicUser(user_id=7, password_hash="argon2-hash")
    assert json.loads(m.to_public_json(user)) == {"userId": 7}
    named = m.PublicUser.model_validate({"userId": 8, "displayName": "Ana"})
    assert json.loads(m.to_public_json(named)) == {"userId": 8, "displayName": "Ana"}


def test_signup_normalizes_email():
    signup = m.Signup(email="  Ana@Example.COM ", password="x" * 12, confirm_password="x" * 12)
    assert signup.email == "ana@example.com"


def test_signup_reports_every_bad_field():
    with pytest.raises(ValidationError) as exc_info:
        m.Signup(email="nope", password="short", confirm_password="short")
    assert {tuple(error["loc"]) for error in exc_info.value.errors()} == {("email",), ("password",)}


def test_signup_passwords_must_match():
    with pytest.raises(ValidationError, match="passwords do not match"):
        m.Signup(email="a@b.io", password="x" * 12, confirm_password="y" * 12)


def test_error_paths():
    assert m.error_paths(ORDER) == []
    bad_item = {"sku": "", "qty": 0, "unit_price": 1}
    assert m.error_paths({**ORDER, "items": [ORDER["items"][0], bad_item]}) == ["items.1.sku", "items.1.qty"]
    assert m.error_paths({"order_id": "o1"}) == ["customer", "items"]


def test_parse_tool_calls():
    calls = m.parse_tool_calls(
        '[{"tool": "weather", "city": "Dubai"}, {"tool": "search", "query": "uv lockfile"}]'
    )
    assert [type(call) for call in calls] == [m.WeatherCall, m.SearchCall]
    assert calls[0].unit == "c"
    assert m.parse_tool_calls("[]") == []


def test_parse_tool_calls_rejects_bad_output():
    with pytest.raises(ValidationError, match="union_tag_invalid"):
        m.parse_tool_calls('[{"tool": "email", "to": "x"}]')
    with pytest.raises(ValidationError, match="json_invalid"):
        m.parse_tool_calls("Sure! Here are the calls: [")
