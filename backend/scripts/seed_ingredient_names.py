import argparse
import asyncio
import json
from pathlib import Path

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.use_cases import register_ingredient_name
from sameplate.domain.recipes.value_objects import IngredientName
from sameplate.infrastructure.config import Settings
from sameplate.infrastructure.db.models.recipes import IngredientNameModel
from sameplate.infrastructure.db.repositories.ingredient_names import (
    SqlAlchemyIngredientNameRepository,
)
from sameplate.infrastructure.db.session import create_db_engine, create_session_factory


def read_ingredient_names(path: Path) -> dict[str, list[str]]:
    data = TypeAdapter(dict[str, list[str]]).validate_python(
        json.loads(path.read_text(encoding="utf-8")), strict=True
    )
    if not data:
        raise ValueError("Expected a nonempty object of ingredient names and synonyms")
    return data


async def insert_ingredient_names(
    session: AsyncSession, names_data: dict[str, list[str]]
) -> None:
    """Register synonyms for existing ingredients in the caller's transaction."""
    repository = SqlAlchemyIngredientNameRepository(session)
    for existing_name, synonyms in names_data.items():
        name = IngredientName(existing_name)
        ingredient_id = await session.scalar(
            select(IngredientNameModel.ingredient_id).where(
                IngredientNameModel.name == name.value
            )
        )
        if ingredient_id is None:
            raise ValueError(
                f"Unknown ingredient {existing_name!r}; load the recipe catalog first"
            )
        for synonym in synonyms:
            await register_ingredient_name(
                ingredient_id, synonym, repository=repository
            )


async def seed_ingredient_names(path: Path) -> None:
    names_data = read_ingredient_names(path)
    settings = Settings()  # pyright: ignore[reportCallIssue]
    engine = create_db_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        async with session_factory.begin() as session:
            await insert_ingredient_names(session, names_data)
        print("Ingredient synonyms loaded successfully.")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load synonyms for existing ingredients. Safe to run repeatedly."
    )
    parser.add_argument("path", type=Path, help="Path to ingredient synonym JSON")
    args = parser.parse_args()
    asyncio.run(seed_ingredient_names(args.path))


if __name__ == "__main__":
    main()
