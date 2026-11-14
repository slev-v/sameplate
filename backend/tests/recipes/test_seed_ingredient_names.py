import json
from pathlib import Path
from runpy import run_path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.use_cases import register_ingredient_name
from sameplate.domain.recipes.exceptions import (
    IngredientNameConflict,
    InvalidIngredientName,
)
from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    IngredientNameModel,
)
from sameplate.infrastructure.db.repositories.ingredient_names import (
    SqlAlchemyIngredientNameRepository,
)


@pytest.fixture(scope="module")
def names_script():
    return run_path(
        str(Path(__file__).resolve().parents[2] / "scripts/seed_ingredient_names.py")
    )


@pytest_asyncio.fixture
async def named_ingredients(db_session: AsyncSession) -> dict[str, int]:
    ingredients = [IngredientModel(name="помидор"), IngredientModel(name="соль")]
    db_session.add_all(ingredients)
    await db_session.flush()
    repository = SqlAlchemyIngredientNameRepository(db_session)
    for ingredient in ingredients:
        await register_ingredient_name(
            ingredient.id, ingredient.name, repository=repository
        )
    return {ingredient.name: ingredient.id for ingredient in ingredients}


@pytest.mark.asyncio
async def test_load_synonyms_is_normalized_and_repeatable(
    db_session: AsyncSession,
    named_ingredients: dict[str, int],
    names_script,
    tmp_path: Path,
):
    path = tmp_path / "ingredient_names.json"
    path.write_text(
        json.dumps({" ПОМИДОР ": ["  ТОМАТ ", "томат", "помидор"]}),
        encoding="utf-8",
    )
    data = names_script["read_ingredient_names"](path)
    await names_script["insert_ingredient_names"](db_session, data)
    await names_script["insert_ingredient_names"](db_session, data)

    rows = await db_session.execute(
        select(IngredientNameModel.name, IngredientNameModel.ingredient_id)
    )
    assert dict(rows.all()) == {
        "помидор": named_ingredients["помидор"],
        "томат": named_ingredients["помидор"],
        "соль": named_ingredients["соль"],
    }
    ingredients = await db_session.scalars(select(IngredientModel.name))
    assert set(ingredients) == {"помидор", "соль"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("last_entry", "error"),
    [
        ({"неизвестный продукт": ["синоним"]}, ValueError),
        ({"соль": ["помидор"]}, IngredientNameConflict),
        ({"соль": ["  "]}, InvalidIngredientName),
    ],
)
async def test_failed_import_rolls_back_all_synonyms(
    db_session: AsyncSession,
    named_ingredients: dict[str, int],
    names_script,
    last_entry: dict[str, list[str]],
    error: type[Exception],
):
    data = {"помидор": ["томат"], **last_entry}
    with pytest.raises(error):
        async with db_session.begin_nested():
            await names_script["insert_ingredient_names"](db_session, data)

    names = await db_session.scalars(select(IngredientNameModel.name))
    assert set(names) == {"помидор", "соль"}


@pytest.mark.parametrize(
    "data", [[], {}, {"помидор": "томат"}, {"помидор": [42]}, {"помидор": None}]
)
def test_reject_invalid_file_structure(names_script, tmp_path: Path, data):
    path = tmp_path / "ingredient_names.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        names_script["read_ingredient_names"](path)
