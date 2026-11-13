from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sameplate.domain.recipes.enums import DifficultyEnum, DishTypeEnum
from sameplate.infrastructure.db.models.recipes import (
    RecipeIngredientModel,
    RecipeModel,
)


async def list_recipes(
    session: AsyncSession,
    *,
    max_time_minutes: int | None = None,
    max_difficulty: DifficultyEnum | None = None,
    dish_type: DishTypeEnum | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[RecipeModel]:
    statement = select(RecipeModel)
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

        statement = statement.where(RecipeModel.difficulty.in_(allowed_difficulties))

    if max_time_minutes is not None:
        statement = statement.where(
            RecipeModel.cooking_time_minutes <= max_time_minutes
        )

    if dish_type is not None:
        statement = statement.where(RecipeModel.dish_type == dish_type)

    statement = statement.order_by(RecipeModel.id).limit(limit).offset(offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_recipe(session: AsyncSession, recipe_id: int) -> RecipeModel | None:
    statement = (
        select(RecipeModel)
        .where(RecipeModel.id == recipe_id)
        .options(
            selectinload(RecipeModel.ingredient_links).selectinload(
                RecipeIngredientModel.ingredient
            )
        )
    )
    result = await session.execute(statement)
    return result.scalars().one_or_none()
