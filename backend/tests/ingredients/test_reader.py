import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.infrastructure.db.models.recipes import IngredientModel
from sameplate.infrastructure.db.readers.ingredients import SqlAlchemyIngredientReader


@pytest.mark.asyncio
async def test_get_existing_ingredient_ids(db_session: AsyncSession):
    first = IngredientModel(name="помидор")
    second = IngredientModel(name="картофель")

    db_session.add_all([first, second])
    await db_session.flush()

    reader = SqlAlchemyIngredientReader(session=db_session)

    unknown_id = max(first.id, second.id) + 1

    result = await reader.get_existing_ids(
        ingredient_ids=frozenset({first.id, unknown_id})
    )

    assert result == frozenset({first.id})
