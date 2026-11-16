from fastapi import APIRouter, HTTPException, status

from sameplate.application.recipes import use_cases
from sameplate.application.recipes.exceptions import UnknownIngredientsError
from sameplate.presentation.api.dependencies import IngredientReaderDep, RecipeReaderDep
from sameplate.presentation.api.recipe_selections.schemas import RecipeSelectionRequest
from sameplate.presentation.api.recipes.schemas import RecipeSummary

router = APIRouter(prefix="/api/v1/recipe-selections", tags=["recipe-selections"])


@router.post("", response_model=list[RecipeSummary])
async def select_recipes(
    ingredient_reader: IngredientReaderDep,
    recipe_reader: RecipeReaderDep,
    request: RecipeSelectionRequest,
) -> list[RecipeSummary]:
    try:
        recipes = await use_cases.select_recipes(
            request.to_dto(),
            ingredient_reader,
            recipe_reader,
        )
    except UnknownIngredientsError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "unknown_ingredients",
                "ingredient_ids": list(exc.unknown_ingredient_ids),
            },
        ) from exc
    return [RecipeSummary.model_validate(recipe) for recipe in recipes]
