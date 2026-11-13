from sameplate.application.recipes.dto import (
    RecipeDetailDTO,
    RecipeFilters,
    RecipeSummaryDTO,
)
from sameplate.application.recipes.ports import IngredientNameRepository, RecipeReader
from sameplate.domain.recipes.exceptions import IngredientNameConflict
from sameplate.domain.recipes.value_objects import IngredientName


async def register_ingredient_name(
    ingredient_id: int,
    name: str,
    *,
    repository: IngredientNameRepository,
) -> None:
    """Register a canonical name or synonym in the caller's transaction."""
    normalized = IngredientName(name)
    if not await repository.assign_name(ingredient_id, normalized):
        raise IngredientNameConflict(
            f"Ingredient name {normalized.value!r} already belongs to another ingredient"
        )


async def list_recipes(
    filters: RecipeFilters, *, reader: RecipeReader
) -> list[RecipeSummaryDTO]:
    return await reader.list_recipes(filters)


async def get_recipe(recipe_id: int, *, reader: RecipeReader) -> RecipeDetailDTO | None:
    return await reader.get_recipe(recipe_id)
