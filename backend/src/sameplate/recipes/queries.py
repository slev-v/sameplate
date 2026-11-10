from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sameplate.recipes.enums import DifficultyEnum, DishTypeEnum
from sameplate.recipes.models import Recipe, RecipeIngredient


async def list_recipes(
    session: AsyncSession,
    *,
    max_time_minutes: int | None = None,
    max_difficulty: DifficultyEnum | None = None,
    dish_type: DishTypeEnum | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Recipe]:
    statement = select(Recipe)
    if max_difficulty is not None:
        allowed_difficulties = {
            DifficultyEnum.EASY: {
                DifficultyEnum.EASY,
            },
            DifficultyEnum.MEDIUM: {
                DifficultyEnum.EASY,
                DifficultyEnum.MEDIUM,
            },
            DifficultyEnum.HARD: {
                DifficultyEnum.EASY,
                DifficultyEnum.MEDIUM,
                DifficultyEnum.HARD,
            },
        }[max_difficulty]

        statement = statement.where(Recipe.difficulty.in_(allowed_difficulties))

    if max_time_minutes is not None:
        statement = statement.where(Recipe.cooking_time_minutes <= max_time_minutes)

    if dish_type is not None:
        statement = statement.where(Recipe.dish_type == dish_type)

    statement = statement.order_by(Recipe.id).limit(limit).offset(offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_recipe(session: AsyncSession, recipe_id: int) -> Recipe | None:
    statement = (
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.ingredient_links).selectinload(
                RecipeIngredient.ingredient
            )
        )
    )
    result = await session.execute(statement)
    return result.scalars().one_or_none()
