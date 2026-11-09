from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from sameplate.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum


class RecipeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str = Field(max_length=150)
    description: str = Field(max_length=500)
    cooking_time_minutes: int = Field(gt=0)
    difficulty: DifficultyEnum
    dish_type: DishTypeEnum
    servings: int = Field(gt=0)
    image_url: str | None


class RecipeIngredientRead(BaseModel):
    ingredient_id: int
    name: str = Field(max_length=150)
    quantity: Decimal | None = Field(gt=0)
    unit: UnitEnum | None
    note: str | None = Field(max_length=250)
    is_required: bool


class RecipeDetail(RecipeSummary):
    instructions: str
    ingredients: list[RecipeIngredientRead]
