from typing import Protocol

from sameplate.application.recipes.dto import (
    RecipeDetailDTO,
    RecipeFilters,
    RecipeSummaryDTO,
)
from sameplate.domain.recipes.value_objects import IngredientName


class IngredientNameRepository(Protocol):
    async def assign_name(self, ingredient_id: int, name: IngredientName) -> bool:
        """Return True for a new/existing assignment, False for a different owner."""
        ...


class RecipeReader(Protocol):
    async def list_recipes(self, filters: RecipeFilters) -> list[RecipeSummaryDTO]: ...

    async def get_recipe(self, recipe_id: int) -> RecipeDetailDTO | None: ...
