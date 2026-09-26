from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.feature_enums import CONSTRUCTIONS, MATERIALS, SEXES, SIZES

MaterialName = Literal[MATERIALS]
Size = Literal[SIZES]
Sex = Literal[SEXES]
Construction = Literal[CONSTRUCTIONS]


class PriceFilter(BaseModel):
    """Price filter in PLN. Convert other currencies to PLN."""

    model_config = ConfigDict(extra="forbid")

    operator: Literal["gt", "lt", "eq"] = Field(
        description="Operator for price filtering. 'gt' = greater than, 'lt' = less than, 'eq' = equal"
    )
    value: float = Field(description="Price value in PLN")


class MaterialFilter(BaseModel):
    """Material composition filter"""

    model_config = ConfigDict(extra="forbid")

    operator: Literal["gt", "lt", "eq", "exists"] = Field(
        description="'gt'/'lt'/'eq' compare material percentage. 'exists' checks if material is present at all."
    )
    key: MaterialName = Field(description="Material name (e.g., 'cotton', 'polyester')")
    percentage: int | None = Field(
        description="Percentage value (0-100) for gt/lt/eq operators. Null for 'exists'.",
    )

    def get_weaviate_property_name(self) -> str:
        return f"{self.key}_percentage"

    @model_validator(mode="before")
    @classmethod
    def set_null_for_missing_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            optional_fields = ["percentage"]
            for field in optional_fields:
                if field not in data:
                    data[field] = None
        return data


class Filters(BaseModel):
    """Structured filters extracted from user query"""

    model_config = ConfigDict(extra="forbid")

    price: PriceFilter | None = Field(description="Price constraint if mentioned")

    sizes: list[Size] | None = Field(
        description="List of clothing sizes that should be available. Can specify multiple, e.g. ['M', 'L']",
    )

    sex: Sex | None = Field(description="Target gender category for the clothing")

    materials: list[MaterialFilter] | None = Field(
        description="Material constraints if mentioned"
    )

    construction: Construction | None = Field(
        description="Fabric construction type (Woven, Knitted, Jersey)"
    )

    color: str | None = Field(
        description="Color preference (e.g., 'red', 'black', 'blue')"
    )

    @model_validator(mode="before")
    @classmethod
    def set_null_for_missing_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            optional_fields = [
                "price",
                "sizes",
                "sex",
                "materials",
                "construction",
                "color",
            ]
            for field in optional_fields:
                if field not in data:
                    data[field] = None
        return data
