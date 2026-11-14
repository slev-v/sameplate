from dataclasses import dataclass
from decimal import Decimal

from sameplate.domain.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum
from sameplate.domain.recipes.value_objects import SelectionPreferences


@dataclass(frozen=True)
class IngredientFilters:
    q: str | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class IngredientDTO:
    id: int
    name: str


@dataclass(frozen=True)
class RecipeFilters:
    max_time_minutes: int | None = None
    max_difficulty: DifficultyEnum | None = None
    dish_type: DishTypeEnum | None = None
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class RecipeSelectionRequestDTO:
    preferences: SelectionPreferences
    max_time_minutes: int | None = None
    max_difficulty: DifficultyEnum | None = None
    dish_type: DishTypeEnum | None = None
    limit: int = 20


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
