from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.dto import (
    RecipeDetailDTO,
    RecipeIngredientDTO,
    RecipeSelectionRequestDTO,
)
from sameplate.domain.recipes.enums import (
    DifficultyEnum,
    DishTypeEnum,
    SelectionModeEnum,
    UnitEnum,
)
from sameplate.domain.recipes.value_objects import SelectionPreferences
from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    RecipeIngredientModel,
    RecipeModel,
)
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("max_missing", "expected"),
    [
        (0, ["complete"]),
        (1, ["complete", "one_missing"]),
        (2, ["complete", "one_missing", "two_missing"]),
    ],
)
async def test_selection_with_missing(
    db_session: AsyncSession,
    selection_data: tuple[dict[str, int], frozenset[int]],
    max_missing: int,
    expected: list[str],
):
    recipe_ids, available_ids = selection_data
    preferences = SelectionPreferences(
        mode=SelectionModeEnum.PANTRY,
        ingredient_ids=available_ids,
        max_missing_ingredients=max_missing,
    )
    request = RecipeSelectionRequestDTO(preferences=preferences)

    reader = SqlAlchemyRecipeReader(db_session)
    recipes = await reader.select_recipes(request)

    expected_ids = [recipe_ids[key] for key in expected]

    assert [recipe.id for recipe in recipes] == expected_ids


@pytest.mark.asyncio
async def test_selection_limit(
    db_session: AsyncSession,
    selection_data: tuple[dict[str, int], frozenset[int]],
):
    recipe_ids, available_ids = selection_data
    preferences = SelectionPreferences(
        mode=SelectionModeEnum.PANTRY,
        ingredient_ids=available_ids,
        max_missing_ingredients=2,
    )
    request = RecipeSelectionRequestDTO(preferences=preferences, limit=1)

    reader = SqlAlchemyRecipeReader(db_session)
    recipes = await reader.select_recipes(request)

    assert [recipe.id for recipe in recipes] == [recipe_ids["complete"]]


@pytest.mark.asyncio
async def test_selection_filters(
    db_session: AsyncSession,
    selection_data: tuple[dict[str, int], frozenset[int]],
):
    _, available_ids = selection_data
    preferences = SelectionPreferences(
        mode=SelectionModeEnum.PANTRY,
        ingredient_ids=available_ids,
        max_missing_ingredients=2,
    )
    request = RecipeSelectionRequestDTO(preferences=preferences, max_time_minutes=10)

    reader = SqlAlchemyRecipeReader(db_session)
    recipes = await reader.select_recipes(request)

    assert recipes == []


@pytest.mark.asyncio
async def test_selection_explore_mode(
    db_session: AsyncSession,
    selection_data: tuple[dict[str, int], frozenset[int]],
):
    preferences = SelectionPreferences(
        mode=SelectionModeEnum.EXPLORE,
    )
    request = RecipeSelectionRequestDTO(preferences=preferences, limit=2)

    reader = SqlAlchemyRecipeReader(db_session)
    recipes = await reader.select_recipes(request)

    assert len(recipes) == 2
    assert recipes[0].id != recipes[1].id
