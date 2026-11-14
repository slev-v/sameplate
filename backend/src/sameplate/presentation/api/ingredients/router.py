from typing import Annotated

from fastapi import APIRouter, Query

from sameplate.application.recipes import use_cases
from sameplate.application.recipes.dto import IngredientFilters
from sameplate.presentation.api.dependencies import IngredientReaderDep
from sameplate.presentation.api.ingredients.schemas import (
    IngredientRead,
    ListIngredientsRequestSchema,
)

router = APIRouter(prefix="/api/v1/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientRead])
async def list_ingredients(
    reader: IngredientReaderDep,
    params: Annotated[ListIngredientsRequestSchema, Query()],
) -> list[IngredientRead]:
    ingredients = await use_cases.list_ingredients(
        IngredientFilters(q=params.q, limit=params.limit, offset=params.offset),
        reader=reader,
    )
    return [IngredientRead.model_validate(ingredient) for ingredient in ingredients]
