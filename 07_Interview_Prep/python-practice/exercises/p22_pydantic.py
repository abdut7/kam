"""Lesson 22: Pydantic in depth.

Run: uv run --with pytest --with fastapi --with httpx pytest tests/test_p22_pydantic.py
(Pydantic is installed together with FastAPI.)

The models are declared for you: read them, they use Field constraints,
ConfigDict, aliases and a discriminated union. Implement every function and
method whose body is `raise NotImplementedError`, top to bottom.
"""
from typing import Annotated, Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel


class LineItem(BaseModel):
    sku: str = Field(min_length=1)
    qty: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: str
    customer: str
    items: list[LineItem] = Field(min_length=1)
    note: str | None = None

    @computed_field
    @property
    def total(self) -> float:
        """Sum of qty * unit_price over all items, rounded to 2 decimals.

        Example: items 2 x 1.50 and 1 x 3.00 -> 6.0
        """
        raise NotImplementedError


def parse_order(raw_json: str, strict: bool = False) -> Order:
    """Validate a JSON string into an Order in one step with
    Order.model_validate_json, passing `strict` through. Let ValidationError
    propagate to the caller.

    Example: items [{"sku": "tea", "qty": "2", "unit_price": 1.5}] -> qty == 2
    in lax mode; strict=True rejects the string "2".
    """
    raise NotImplementedError


class PublicUser(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    user_id: int
    display_name: str | None = None
    password_hash: str = ""


def to_public_json(user: PublicUser) -> str:
    """Serialize to a JSON string with camelCase keys, leaving out password_hash
    and every field whose value is None.

    Example: PublicUser(user_id=7, password_hash="x") -> '{"userId":7}'
    """
    raise NotImplementedError


class Signup(BaseModel):
    email: str
    password: str = Field(min_length=12)
    confirm_password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Strip surrounding spaces and lowercase. Raise ValueError("email must
        contain @") when there is no "@".

        Example: "  Ana@Example.COM " -> "ana@example.com"
        """
        raise NotImplementedError

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        """Raise ValueError("passwords do not match") when password and
        confirm_password differ; otherwise return self.

        Example: password "x" * 12 with confirm_password "y" * 12 -> ValidationError
        """
        raise NotImplementedError


def error_paths(data: dict[str, Any]) -> list[str]:
    """Validate `data` as an Order and return every error location as a dotted
    path, in the order Pydantic reports them. Return [] when the data is valid.

    Example: second item has qty 0 -> ["items.1.qty"]
    """
    raise NotImplementedError


class SearchCall(BaseModel):
    tool: Literal["search"]
    query: str = Field(min_length=1)


class WeatherCall(BaseModel):
    tool: Literal["weather"]
    city: str
    unit: Literal["c", "f"] = "c"


ToolCall = Annotated[SearchCall | WeatherCall, Field(discriminator="tool")]


def parse_tool_calls(raw_json: str) -> list[SearchCall | WeatherCall]:
    """Validate a JSON array of tool calls produced by an LLM. The "tool" field
    picks the model. Use a TypeAdapter for list[ToolCall] (build it once, at
    module level). Let ValidationError propagate.

    Example: '[{"tool": "weather", "city": "Dubai"}]'
    -> [WeatherCall(tool="weather", city="Dubai", unit="c")]
    """
    raise NotImplementedError
