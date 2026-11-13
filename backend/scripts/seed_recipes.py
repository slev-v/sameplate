import argparse
import asyncio
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.core.config import Settings
from sameplate.infrastructure.db.session import create_db_engine, create_session_factory
from sameplate.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum
from sameplate.recipes.models import Ingredient, Recipe, RecipeIngredient


async def insert_recipes(
    session: AsyncSession,
    recipes_data: list[dict],
) -> None:
    existing_recipe_id = await session.scalar(select(Recipe.id).limit(1))
    if existing_recipe_id is not None:
        raise ValueError("Каталог уже содержит рецепты. Начальная загрузка отменена.")

    existing_ingredients = await session.scalars(select(Ingredient))
    ingredients_by_name = {
        ingredient.name: ingredient for ingredient in existing_ingredients
    }

    for data in recipes_data:
        recipe = Recipe(
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
            name = item["name"].strip().casefold()
            if not name:
                raise ValueError("Название ингредиента не может быть пустым.")

            ingredient = ingredients_by_name.get(name)

            if ingredient is None:
                ingredient = Ingredient(name=name)
                ingredients_by_name[name] = ingredient

            quantity = (
                Decimal(item["quantity"]) if item["quantity"] is not None else None
            )
            unit = UnitEnum(item["unit"]) if item["unit"] is not None else None

            recipe.ingredient_links.append(
                RecipeIngredient(
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
