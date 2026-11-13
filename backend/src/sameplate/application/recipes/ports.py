from typing import Protocol

from sameplate.domain.recipes.value_objects import IngredientName


class IngredientNameRepository(Protocol):
    async def assign_name(self, ingredient_id: int, name: IngredientName) -> bool:
        """Return True for a new/existing assignment, False for a different owner."""
        ...
