from dataclasses import replace

from sameplate.application.recipes.dto import (
    IngredientDTO,
    IngredientFilters,
    RecipeDetailDTO,
    RecipeFilters,
    RecipeSelectionRequestDTO,
    RecipeSummaryDTO,
)
from sameplate.application.recipes.exceptions import UnknownIngredientsError
from sameplate.application.recipes.ports import (
    IngredientNameRepository,
    IngredientReader,
    RecipeReader,
)
from sameplate.domain.recipes.enums import SelectionModeEnum
from sameplate.domain.recipes.exceptions import IngredientNameConflict
from sameplate.domain.recipes.value_objects import IngredientName, SelectionPreferences


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


async def list_ingredients(
    filters: IngredientFilters, *, reader: IngredientReader
) -> list[IngredientDTO]:
    q = IngredientName(filters.q).value if filters.q and filters.q.strip() else None
    if q is not None:
        # Search equivalence leaves registered ingredient names unchanged.
        q = q.replace("ё", "е")
    return await reader.list_ingredients(replace(filters, q=q))


async def validate_selection_ingredients(
    preferences: SelectionPreferences, *, reader: IngredientReader
) -> None:
    if preferences.mode == SelectionModeEnum.EXPLORE:
        return

    unknown_ingredient_ids = preferences.ingredient_ids - await reader.get_existing_ids(
        ingredient_ids=preferences.ingredient_ids
    )

    if unknown_ingredient_ids:
        raise UnknownIngredientsError(unknown_ingredient_ids)


async def select_recipes(
    request: RecipeSelectionRequestDTO,
    ingredient_reader: IngredientReader,
    recipe_reader: RecipeReader,
) -> list[RecipeSummaryDTO]:
    preferences = request.preferences
    await validate_selection_ingredients(preferences, reader=ingredient_reader)

    return await recipe_reader.select_recipes(request)
