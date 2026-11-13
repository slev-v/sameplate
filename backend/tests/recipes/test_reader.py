from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.dto import RecipeDetailDTO, RecipeIngredientDTO
from sameplate.infrastructure.db.readers.recipes import SqlAlchemyRecipeReader


@pytest.mark.asyncio
async def test_recipe_detail_is_independent_of_session(
    db_session: AsyncSession, recipe_ids: dict[str, int]
):
    connection = await db_session.connection()
    async with AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint"
    ) as session:
        reader = SqlAlchemyRecipeReader(session)
        recipe = await reader.get_recipe(recipe_ids["quick_easy_main"])
        session.expire_all()

    assert isinstance(recipe, RecipeDetailDTO)
    assert recipe.id == recipe_ids["quick_easy_main"]
    assert recipe.title == "First recipe"
    assert recipe.instructions == "Cook your dish"
    assert isinstance(recipe.ingredients, tuple)
    assert all(isinstance(item, RecipeIngredientDTO) for item in recipe.ingredients)
    ingredients = {item.name: item for item in recipe.ingredients}
    assert ingredients["flour"].quantity == Decimal("0.500")
    assert ingredients["salt"].quantity is None
    assert ingredients["salt"].note == "To taste"
