from dataclasses import dataclass
from decimal import Decimal

from sameplate.domain.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum


@dataclass(frozen=True)
class RecipeFilters:
    max_time_minutes: int | None = None
    max_difficulty: DifficultyEnum | None = None
    dish_type: DishTypeEnum | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class RecipeSummaryDTO:
    id: int
    title: str
    description: str
    cooking_time_minutes: int
    difficulty: DifficultyEnum
    dish_type: DishTypeEnum
    servings: int
    image_url: str | None


@dataclass(frozen=True)
class RecipeIngredientDTO:
    ingredient_id: int
    name: str
    quantity: Decimal | None
    unit: UnitEnum | None
    note: str | None
    is_required: bool


@dataclass(frozen=True)
class RecipeDetailDTO(RecipeSummaryDTO):
    instructions: str
    ingredients: tuple[RecipeIngredientDTO, ...]
