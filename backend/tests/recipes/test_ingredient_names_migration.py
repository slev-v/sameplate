from pathlib import Path
from runpy import run_path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Connection, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    IngredientNameModel,
)

pytestmark = pytest.mark.asyncio


async def run_upgrade(session: AsyncSession) -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic/versions/92a731b8f2d0_add_ingredient_names.py"
    )
    migration = run_path(str(path))

    def upgrade(connection: Connection) -> None:
        with Operations.context(MigrationContext.configure(connection)):
            migration["upgrade"]()

    connection = await session.connection()
    await connection.run_sync(upgrade)


async def test_backfill_existing_canonical_names(db_session: AsyncSession):
    # Simulate the previous schema inside the test's rollback transaction.
    await db_session.execute(text("DROP TABLE ingredient_names"))
    ingredient = IngredientModel(name="  КУРИНОЕ   ФИЛЕ ")
    db_session.add(ingredient)
    await db_session.flush()

    await run_upgrade(db_session)

    row = await db_session.scalar(select(IngredientNameModel))
    assert row is not None
    assert row.name == "куриное филе"
    assert row.ingredient_id == ingredient.id
    assert ingredient.name == "  КУРИНОЕ   ФИЛЕ "


async def test_backfill_refuses_ambiguous_names(db_session: AsyncSession):
    await db_session.execute(text("DROP TABLE ingredient_names"))
    db_session.add_all(
        [IngredientModel(name="помидор"), IngredientModel(name=" Помидор ")]
    )
    await db_session.flush()

    with pytest.raises(ValueError, match="same normalized name"):
        await run_upgrade(db_session)
