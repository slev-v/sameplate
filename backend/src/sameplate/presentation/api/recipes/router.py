from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from sameplate.application.recipes import use_cases
from sameplate.application.recipes.dto import RecipeFilters
from sameplate.presentation.api.dependencies import RecipeReaderDep
from sameplate.presentation.api.recipes.schemas import (
    ListRecipesRequestSchema,
    RecipeDetail,
    RecipeSummary,
)

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeSummary])
async def list_recipes(
    reader: RecipeReaderDep,
    params: Annotated[ListRecipesRequestSchema, Query()],
) -> list[RecipeSummary]:
    filters = RecipeFilters(
        max_time_minutes=params.max_time_minutes,
        max_difficulty=params.max_difficulty,
        dish_type=params.dish_type,
        limit=params.limit,
        offset=params.offset,
    )
    recipes = await use_cases.list_recipes(filters, reader=reader)
    return [RecipeSummary.model_validate(recipe) for recipe in recipes]


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe(
    recipe_id: Annotated[int, Path(gt=0, le=2_147_483_647)], reader: RecipeReaderDep
) -> RecipeDetail:
    recipe = await use_cases.get_recipe(recipe_id, reader=reader)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )
    return RecipeDetail.model_validate(recipe)
