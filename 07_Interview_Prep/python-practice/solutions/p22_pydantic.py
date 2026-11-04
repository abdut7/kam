"""Lesson 22 reference solutions: Pydantic in depth."""
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

    @computed_field  # included in model_dump, JSON output and the serialization schema
    @property
    def total(self) -> float:
        # round: 3 * 0.1 is 0.30000000000000004 in binary floating point.
        return round(sum(item.qty * item.unit_price for item in self.items), 2)


def parse_order(raw_json: str, strict: bool = False) -> Order:
    # model_validate_json parses and validates in one pass inside pydantic-core,
    # faster than json.loads followed by model_validate.
    return Order.model_validate_json(raw_json, strict=strict)


class PublicUser(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    user_id: int
    display_name: str | None = None
    password_hash: str = ""


def to_public_json(user: PublicUser) -> str:
    return user.model_dump_json(by_alias=True, exclude={"password_hash"}, exclude_none=True)


class Signup(BaseModel):
    email: str
    password: str = Field(min_length=12)
    confirm_password: str

    @field_validator("email")  # mode="after" by default: value is already a str
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value:
            raise ValueError("email must contain @")  # becomes a value_error entry
        return value

    @model_validator(mode="after")  # runs once every field is valid
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        return self


def error_paths(data: dict[str, Any]) -> list[str]:
    try:
        Order.model_validate(data)
    except ValidationError as exc:
        # loc is a tuple such as ("items", 1, "qty"); ints are list indexes.
        return [".".join(str(part) for part in error["loc"]) for error in exc.errors()]
    return []


class SearchCall(BaseModel):
    tool: Literal["search"]
    query: str = Field(min_length=1)


class WeatherCall(BaseModel):
    tool: Literal["weather"]
    city: str
    unit: Literal["c", "f"] = "c"


ToolCall = Annotated[SearchCall | WeatherCall, Field(discriminator="tool")]

# Building a TypeAdapter compiles a validator, so do it once, not per call.
_TOOL_CALLS = TypeAdapter(list[ToolCall])


def parse_tool_calls(raw_json: str) -> list[SearchCall | WeatherCall]:
    return _TOOL_CALLS.validate_json(raw_json)
