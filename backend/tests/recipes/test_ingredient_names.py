from pathlib import Path
from runpy import run_path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.use_cases import register_ingredient_name
from sameplate.domain.recipes.exceptions import IngredientNameConflict
from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    IngredientNameModel,
    RecipeIngredientModel,
)
from sameplate.infrastructure.db.repositories.ingredient_names import (
    SqlAlchemyIngredientNameRepository,
)

pytestmark = pytest.mark.asyncio


async def test_register_canonical_name_and_synonym(db_session: AsyncSession):
    repository = SqlAlchemyIngredientNameRepository(db_session)
    ingredient = IngredientModel(name="помидор")
    db_session.add(ingredient)
    await db_session.flush()

    await register_ingredient_name(ingredient.id, "Помидор", repository=repository)
    await register_ingredient_name(ingredient.id, " ТОМАТ ", repository=repository)
    await register_ingredient_name(ingredient.id, "томат", repository=repository)

    names = await db_session.scalars(
        select(IngredientNameModel.name).where(
            IngredientNameModel.ingredient_id == ingredient.id
        )
    )
    assert set(names) == {"помидор", "томат"}


async def test_name_cannot_belong_to_two_ingredients(db_session: AsyncSession):
    repository = SqlAlchemyIngredientNameRepository(db_session)
    first = IngredientModel(name="помидор")
    second = IngredientModel(name="картофель")
    db_session.add_all([first, second])
    await db_session.flush()
    await register_ingredient_name(first.id, "томат", repository=repository)

    with pytest.raises(IngredientNameConflict):
        await register_ingredient_name(second.id, " ТОМАТ ", repository=repository)

    assert (
        await db_session.scalar(select(func.count()).select_from(IngredientNameModel))
        == 1
    )


async def test_seed_reuses_ingredient_by_synonym(db_session: AsyncSession):
    repository = SqlAlchemyIngredientNameRepository(db_session)
    ingredient = IngredientModel(name="помидор")
    db_session.add(ingredient)
    await db_session.flush()
    await register_ingredient_name(ingredient.id, "помидор", repository=repository)
    await register_ingredient_name(ingredient.id, "томат", repository=repository)

    script = run_path(
        str(Path(__file__).resolve().parents[2] / "scripts/seed_recipes.py")
    )
    await script["insert_recipes"](
        db_session,
        [
            {
                "title": "Салат",
                "description": "Описание",
                "instructions": "Нарезать",
                "cooking_time_minutes": 5,
                "difficulty": "easy",
                "dish_type": "salad",
                "servings": 1,
                "image_url": None,
                "ingredients": [
                    {
                        "name": " ТОМАТ ",
                        "quantity": "1",
                        "unit": "piece",
                        "note": None,
                        "is_required": True,
                    }
                ],
            }
        ],
    )
    await db_session.flush()

    assert (
        await db_session.scalar(select(func.count()).select_from(IngredientModel)) == 1
    )
    assert (
        await db_session.scalar(select(RecipeIngredientModel.ingredient_id))
        == ingredient.id
    )
