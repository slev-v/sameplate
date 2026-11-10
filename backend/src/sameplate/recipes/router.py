from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from sameplate.core.dependencies import SessionDep
from sameplate.recipes import queries
from sameplate.recipes.schemas import (
    ListRecipesRequestSchema,
    RecipeDetail,
    RecipeIngredientRead,
    RecipeSummary,
)

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeSummary])
async def list_recipes(
    session: SessionDep,
    params: Annotated[ListRecipesRequestSchema, Query()],
) -> list[RecipeSummary]:
    recipes = await queries.list_recipes(
        session,
        max_time_minutes=params.max_time_minutes,
        max_difficulty=params.max_difficulty,
        dish_type=params.dish_type,
        limit=params.limit,
        offset=params.offset,
    )

    return [RecipeSummary.model_validate(recipe) for recipe in recipes]


@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe(
    recipe_id: Annotated[int, Path(gt=0)], session: SessionDep
) -> RecipeDetail:
    recipe = await queries.get_recipe(session, recipe_id)

    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    summary = RecipeSummary.model_validate(recipe)

    ingredients = [
        RecipeIngredientRead(
            ingredient_id=link.ingredient_id,
            name=link.ingredient.name,
            quantity=link.quantity,
            unit=link.unit,
            note=link.note,
            is_required=link.is_required,
        )
        for link in recipe.ingredient_links
    ]

    return RecipeDetail(
        **summary.model_dump(),
        instructions=recipe.instructions,
        ingredients=ingredients,
    )
