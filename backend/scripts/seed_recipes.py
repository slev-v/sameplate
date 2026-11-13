import argparse
import asyncio
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.use_cases import register_ingredient_name
from sameplate.core.config import Settings
from sameplate.domain.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum
from sameplate.domain.recipes.value_objects import IngredientName
from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    IngredientNameModel,
    RecipeIngredientModel,
    RecipeModel,
)
from sameplate.infrastructure.db.repositories.ingredient_names import (
    SqlAlchemyIngredientNameRepository,
)
from sameplate.infrastructure.db.session import create_db_engine, create_session_factory


async def insert_recipes(
    session: AsyncSession,
    recipes_data: list[dict],
) -> None:
    repository = SqlAlchemyIngredientNameRepository(session)
    existing_recipe_id = await session.scalar(select(RecipeModel.id).limit(1))
    if existing_recipe_id is not None:
        raise ValueError("Каталог уже содержит рецепты. Начальная загрузка отменена.")

    existing_names = await session.execute(
        select(IngredientNameModel.name, IngredientModel).join(IngredientModel)
    )
    ingredients_by_name = {name: ingredient for name, ingredient in existing_names}

    for data in recipes_data:
        recipe = RecipeModel(
            title=data["title"],
            description=data["description"],
            instructions=data["instructions"],
            cooking_time_minutes=data["cooking_time_minutes"],
            difficulty=DifficultyEnum(data["difficulty"]),
            dish_type=DishTypeEnum(data["dish_type"]),
            servings=data["servings"],
            image_url=data["image_url"],
        )

        for item in data["ingredients"]:
            name = IngredientName(item["name"]).value

            ingredient = ingredients_by_name.get(name)

            if ingredient is None:
                ingredient = IngredientModel(name=name)
                session.add(ingredient)
                await session.flush()
                await register_ingredient_name(
                    ingredient.id, name, repository=repository
                )
                ingredients_by_name[name] = ingredient

            quantity = (
                Decimal(item["quantity"]) if item["quantity"] is not None else None
            )
            unit = UnitEnum(item["unit"]) if item["unit"] is not None else None

            recipe.ingredient_links.append(
                RecipeIngredientModel(
                    ingredient=ingredient,
                    quantity=quantity,
                    unit=unit,
                    note=item["note"],
                    is_required=item["is_required"],
                )
            )

        session.add(recipe)


async def seed_recipes(path: Path) -> None:
    recipes_data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(recipes_data, list) or not recipes_data:
        raise ValueError("Ожидается непустой JSON-массив рецептов.")

    settings = Settings()  # pyright: ignore[reportCallIssue]
    engine = create_db_engine(settings)

    try:
        session_factory = create_session_factory(engine)

        async with session_factory.begin() as session:
            await insert_recipes(session, recipes_data)

        print(f"Загружено рецептов: {len(recipes_data)}")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Первоначальная загрузка рецептов в dev-базу.",
    )
    parser.add_argument("path", type=Path, help="Путь к JSON с рецептами")
    args = parser.parse_args()

    asyncio.run(seed_recipes(args.path))


if __name__ == "__main__":
    main()
