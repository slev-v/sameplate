from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.domain.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum
from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    RecipeIngredientModel,
    RecipeModel,
)


@pytest_asyncio.fixture
async def recipe_ids(db_session: AsyncSession) -> dict[str, int]:
    ingredient = IngredientModel(name="flour")

    first = RecipeModel(
        title="First recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.MAIN,
        servings=1,
        image_url=None,
        ingredient_links=[
            RecipeIngredientModel(
                ingredient=ingredient,
                quantity=Decimal("0.500"),
                unit=UnitEnum.TABLESPOON,
                note=None,
                is_required=True,
            ),
            RecipeIngredientModel(
                ingredient=IngredientModel(name="salt"),
                quantity=None,
                unit=None,
                note="To taste",
                is_required=False,
            ),
        ],
    )
    second = RecipeModel(
        title="Second recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=30,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.MAIN,
        servings=2,
        image_url=None,
    )
    third = RecipeModel(
        title="Third recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.MEDIUM,
        dish_type=DishTypeEnum.MAIN,
        servings=2,
        image_url=None,
    )
    fourth = RecipeModel(
        title="Fourth recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.SALAD,
        servings=2,
        image_url=None,
    )
    fifth = RecipeModel(
        title="Fifth recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=45,
        difficulty=DifficultyEnum.HARD,
        dish_type=DishTypeEnum.SOUP,
        servings=2,
        image_url=None,
    )

    db_session.add_all([first, second, third, fourth, fifth])
    await db_session.flush()

    ids = {
        "quick_easy_main": first.id,
        "slow_easy_main": second.id,
        "quick_medium_main": third.id,
        "quick_easy_salad": fourth.id,
        "slow_hard_soup": fifth.id,
    }

    db_session.expunge_all()

    return ids


@pytest_asyncio.fixture
async def selection_data(
    db_session: AsyncSession,
) -> tuple[dict[str, int], frozenset[int]]:
    egg = IngredientModel(name="яйцо")
    milk = IngredientModel(name="молоко")
    flour = IngredientModel(name="мука")
    salt = IngredientModel(name="соль")

    first = RecipeModel(
        title="Third recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.MAIN,
        servings=1,
        image_url=None,
        ingredient_links=[
            RecipeIngredientModel(
                ingredient=egg,
                quantity=Decimal(1),
                unit=UnitEnum.PIECE,
                note=None,
                is_required=True,
            ),
            RecipeIngredientModel(
                ingredient=milk,
                quantity=Decimal(150),
                unit=UnitEnum.MILLILITER,
                note=None,
                is_required=True,
            ),
            RecipeIngredientModel(
                ingredient=flour,
                quantity=Decimal(500),
                unit=UnitEnum.GRAM,
                note=None,
                is_required=True,
            ),
        ],
    )
    second = RecipeModel(
        title="Second recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.MAIN,
        servings=1,
        image_url=None,
        ingredient_links=[
            RecipeIngredientModel(
                ingredient=egg,
                quantity=Decimal(1),
                unit=UnitEnum.PIECE,
                note=None,
                is_required=True,
            ),
            RecipeIngredientModel(
                ingredient=milk,
                quantity=Decimal(150),
                unit=UnitEnum.MILLILITER,
                note=None,
                is_required=True,
            ),
        ],
    )
    third = RecipeModel(
        title="First recipe",
        description="Recipe for ingredient tests",
        instructions="Cook your dish",
        cooking_time_minutes=15,
        difficulty=DifficultyEnum.EASY,
        dish_type=DishTypeEnum.MAIN,
        servings=1,
        image_url=None,
        ingredient_links=[
            RecipeIngredientModel(
                ingredient=egg,
                quantity=Decimal(1),
                unit=UnitEnum.PIECE,
                note=None,
                is_required=True,
            ),
            RecipeIngredientModel(
                ingredient=salt,
                quantity=None,
                unit=None,
                note="To taste",
                is_required=False,
            ),
        ],
    )

    db_session.add_all([first, second, third])
    await db_session.flush()

    ids = {
        "two_missing": first.id,
        "one_missing": second.id,
        "complete": third.id,
    }

    available_ids = frozenset({egg.id})

    db_session.expunge_all()

    return ids, available_ids
