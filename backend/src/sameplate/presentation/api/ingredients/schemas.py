from pydantic import BaseModel, ConfigDict, Field, field_validator

from sameplate.domain.recipes.value_objects import IngredientName


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ListIngredientsRequestSchema(BaseModel):
    q: str | None = Field(default=None, max_length=150)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=2_147_483_647)

    @field_validator("q")
    @classmethod
    def normalize_query(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return IngredientName(value).value
