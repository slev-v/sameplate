import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum
from sameplate.recipes.models import Ingredient, Recipe, RecipeIngredient


@pytest_asyncio.fixture
async def recipe_ids(db_session: AsyncSession) -> list[int]:
    ingredient = Ingredient(name="flour")

    first = Recipe(
        title="First recipe",
        description="Recipe for ingridient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.MAIN,
        servings=1,
        image_url=None,
        ingredient_links=[
            RecipeIngredient(
                ingredient=ingredient,
                quantity="0.500",
                unit=UnitEnum.TABLESPOON,
                note=None,
                is_required=True,
            )
        ],
    )
    second = Recipe(
        title="Second recipe",
        description="Recipe for ingridient tests",
        instructions="Cook your dish",
        cooking_time_minutes=30,
        difficulty=DifficultyEnum.MEDIUM,
        dish_type=DishTypeEnum.SNACK,
        servings=2,
        image_url=None,
    )

    db_session.add_all([first, second])
    await db_session.flush()

    ids = [first.id, second.id]

    db_session.expunge_all()

    return ids
