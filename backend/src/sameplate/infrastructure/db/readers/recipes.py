from dataclasses import asdict

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sameplate.application.recipes.dto import (
    RecipeDetailDTO,
    RecipeFilters,
    RecipeIngredientDTO,
    RecipeSelectionRequestDTO,
    RecipeSummaryDTO,
)
from sameplate.domain.recipes.enums import (
    DifficultyEnum,
    DishTypeEnum,
    SelectionModeEnum,
)
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


def _apply_recipe_filters(
    statement: Select[RecipeModel],
    *,
    max_time_minutes: int | None,
    max_difficulty: DifficultyEnum | None,
    dish_type: DishTypeEnum | None,
) -> Select[RecipeModel]:
    if max_difficulty is not None:
        allowed_difficulties = {
            DifficultyEnum.EASY: {DifficultyEnum.EASY},
            DifficultyEnum.MEDIUM: {DifficultyEnum.EASY, DifficultyEnum.MEDIUM},
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
    return statement


class SqlAlchemyRecipeReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recipes(self, filters: RecipeFilters) -> list[RecipeSummaryDTO]:
        statement = select(RecipeModel)
        statement = _apply_recipe_filters(
            statement,
            max_time_minutes=filters.max_time_minutes,
            max_difficulty=filters.max_difficulty,
            dish_type=filters.dish_type,
        )
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

    async def select_recipes(
        self, request: RecipeSelectionRequestDTO
    ) -> list[RecipeSummaryDTO]:
        statement = select(RecipeModel)
        statement = _apply_recipe_filters(
            statement,
            max_time_minutes=request.max_time_minutes,
            max_difficulty=request.max_difficulty,
            dish_type=request.dish_type,
        )

        preferences = request.preferences

        if request.preferences.mode == SelectionModeEnum.PANTRY:
            max_missing = preferences.max_missing_ingredients
            assert max_missing is not None

            missing_count = func.count(RecipeIngredientModel.ingredient_id)

            statement = (
                statement.outerjoin(
                    RecipeIngredientModel,
                    and_(
                        RecipeIngredientModel.recipe_id == RecipeModel.id,
                        RecipeIngredientModel.is_required.is_(True),
                        RecipeIngredientModel.ingredient_id.not_in(
                            preferences.ingredient_ids
                        ),
                    ),
                )
                .group_by(RecipeModel.id)
                .having(missing_count <= max_missing)
                .order_by(missing_count, RecipeModel.id)
            )

        else:
            statement = statement.order_by(func.random())
        statement = statement.limit(request.limit)

        recipes = await self._session.scalars(statement)
        return [_summary(recipe) for recipe in recipes]
