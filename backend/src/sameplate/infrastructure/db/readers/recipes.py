from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sameplate.application.recipes.dto import (
    RecipeDetailDTO,
    RecipeFilters,
    RecipeIngredientDTO,
    RecipeSummaryDTO,
)
from sameplate.domain.recipes.enums import DifficultyEnum
from sameplate.infrastructure.db.models.recipes import (
    RecipeIngredientModel,
    RecipeModel,
)


def _summary(recipe: RecipeModel) -> RecipeSummaryDTO:
    return RecipeSummaryDTO(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        cooking_time_minutes=recipe.cooking_time_minutes,
        difficulty=recipe.difficulty,
        dish_type=recipe.dish_type,
        servings=recipe.servings,
        image_url=recipe.image_url,
    )


class SqlAlchemyRecipeReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recipes(self, filters: RecipeFilters) -> list[RecipeSummaryDTO]:
        statement = select(RecipeModel)
        if filters.max_difficulty is not None:
            allowed_difficulties = {
                DifficultyEnum.EASY: {DifficultyEnum.EASY},
                DifficultyEnum.MEDIUM: {DifficultyEnum.EASY, DifficultyEnum.MEDIUM},
                DifficultyEnum.HARD: {
                    DifficultyEnum.EASY,
                    DifficultyEnum.MEDIUM,
                    DifficultyEnum.HARD,
                },
            }[filters.max_difficulty]
            statement = statement.where(
                RecipeModel.difficulty.in_(allowed_difficulties)
            )
        if filters.max_time_minutes is not None:
            statement = statement.where(
                RecipeModel.cooking_time_minutes <= filters.max_time_minutes
            )
        if filters.dish_type is not None:
            statement = statement.where(RecipeModel.dish_type == filters.dish_type)
        statement = (
            statement.order_by(RecipeModel.id)
            .limit(filters.limit)
            .offset(filters.offset)
        )
        recipes = await self._session.scalars(statement)
        return [_summary(recipe) for recipe in recipes]

    async def get_recipe(self, recipe_id: int) -> RecipeDetailDTO | None:
        statement = (
            select(RecipeModel)
            .where(RecipeModel.id == recipe_id)
            .options(
                selectinload(RecipeModel.ingredient_links).selectinload(
                    RecipeIngredientModel.ingredient
                )
            )
        )
        recipe = await self._session.scalar(statement)
        if recipe is None:
            return None
        return RecipeDetailDTO(
            **asdict(_summary(recipe)),
            instructions=recipe.instructions,
            ingredients=tuple(
                RecipeIngredientDTO(
                    ingredient_id=link.ingredient_id,
                    name=link.ingredient.name,
                    quantity=link.quantity,
                    unit=link.unit,
                    note=link.note,
                    is_required=link.is_required,
                )
                for link in recipe.ingredient_links
            ),
        )
