from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sameplate.recipes.models import Recipe, RecipeIngredient


async def list_recipes(
    session: AsyncSession, *, limit: int = 20, offset: int = 0
) -> list[Recipe]:
    statement = select(Recipe).order_by(Recipe.id).limit(limit).offset(offset)
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
