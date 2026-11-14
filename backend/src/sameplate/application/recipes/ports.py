from typing import Protocol

from sameplate.application.recipes.dto import (
    IngredientDTO,
    IngredientFilters,
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


class IngredientReader(Protocol):
    async def list_ingredients(self, filters: IngredientFilters) -> list[IngredientDTO]:
        """Read a page using a normalized query, or None for the full catalog."""
        ...

    async def get_existing_ids(
        self, ingredient_ids: frozenset[int]
    ) -> frozenset[int]: ...
